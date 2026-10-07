import json
import io
import os
import logging
import shutil
import subprocess
import tempfile
import mimetypes
import uuid
import requests
from flask import Blueprint, request, jsonify, g, send_file, send_from_directory
from flask_babel import gettext as _
from contextlib import closing
import sqlite3
import config_manager
from anx_library import (
    get_anx_user_dirs,
    process_anx_import_folder,
    update_anx_book_metadata,
    delete_anx_book,
    get_anx_book_details
)
from .calibre import download_calibre_book, get_calibre_book_details
from .email_service import send_email_with_config
from epub_fixer import fix_epub_for_kindle
from utils.auth import get_calibre_auth
from utils.covers import get_calibre_cover_data
from utils.text import random_english_text, safe_title, safe_author
from utils.activity_logger import log_activity, ActivityType
from utils.library_provider import get_provider

books_bp = Blueprint('books', __name__, url_prefix='/api')

@books_bp.route('/download_anx_book/<int:book_id>', methods=['GET'])
def download_anx_book_api(book_id):
    dirs = get_anx_user_dirs(g.user.username)
    if not dirs or not os.path.exists(dirs["db_path"]):
        error_msg = _('Anx database not found.')
        log_activity(ActivityType.DOWNLOAD_BOOK, book_id=book_id, library_type='anx', success=False, failure_reason=error_msg)
        return jsonify({'error': error_msg}), 404
        
    try:
        with closing(sqlite3.connect(dirs["db_path"])) as db:
            db.row_factory = sqlite3.Row
            cursor = db.cursor()
            cursor.execute("SELECT file_path, title FROM tb_books WHERE id = ?", (book_id,))
            book_row = cursor.fetchone()
            if not book_row or not book_row['file_path']:
                error_msg = _('Book file with ID %(book_id)s not found.', book_id=book_id)
                log_activity(ActivityType.DOWNLOAD_BOOK, book_id=book_id, library_type='anx', success=False, failure_reason=error_msg)
                return jsonify({'error': error_msg}), 404
            
            log_activity(ActivityType.DOWNLOAD_BOOK, book_id=book_id, book_title=book_row['title'], library_type='anx', success=True)
            
            data_dir = dirs["workspace"]
            return send_from_directory(data_dir, book_row['file_path'], as_attachment=True)
            
    except Exception as e:
        print(f"Error downloading anx book {book_id} for user {g.user.username}: {e}")
        error_msg = _('Error downloading book: %(error)s', error=e)
        log_activity(ActivityType.DOWNLOAD_BOOK, book_id=book_id, library_type='anx', success=False, failure_reason=error_msg)
        return jsonify({'error': error_msg}), 500

def _get_processed_epub_for_book(book_id, user_dict, filename_format='title - author', language='zh'):
    """
    Core logic to get a processed EPUB for a book.
    It handles downloading, converting (if necessary), and fixing the EPUB.
    Returns a tuple: (content, filename, needs_conversion_flag) or (None, None, None) on error.
    """
    details = get_calibre_book_details(book_id)
    if not details:
        logging.error(f"Could not get details for book_id {book_id}")
        return None, None, False

    available_formats = [f.lower() for f in details.get('formats', [])]
    needs_conversion = False
    
    with tempfile.TemporaryDirectory() as temp_dir:
        epub_to_process_path = None
        
        # Check if EPUB already exists
        if 'epub' in available_formats:
            logging.info(f"Book ID {book_id} has EPUB format. Downloading directly.")
            content, filename = download_calibre_book(book_id, 'epub')
            if not content:
                logging.error(f"Failed to download existing EPUB for book_id {book_id}")
                return None, None, False
            
            epub_to_process_path = os.path.join(temp_dir, filename)
            with open(epub_to_process_path, 'wb') as f:
                f.write(content)
        else:
            # If no EPUB, convert from another format
            needs_conversion = True
            if not shutil.which('ebook-converter'):
                logging.error("ebook-converter not found, but conversion is needed.")
                return None, "CONVERTER_NOT_FOUND", False

            priority_str = user_dict.get('send_format_priority') or '[]'
            priority = json.loads(priority_str)
            format_to_convert = next((f for f in priority if f.lower() in available_formats), available_formats[0] if available_formats else None)

            if not format_to_convert:
                logging.error(f"No suitable format found to convert from for book_id {book_id}")
                return None, None, False

            logging.info(f"Book ID {book_id} needs conversion. Converting from {format_to_convert}.")
            original_content, original_filename = download_calibre_book(book_id, format_to_convert)
            if not original_content:
                logging.error(f"Failed to download source format {format_to_convert} for book_id {book_id}")
                return None, None, False

            source_path = os.path.join(temp_dir, original_filename)
            with open(source_path, 'wb') as f:
                f.write(original_content)

            base_name, _unused = os.path.splitext(original_filename)
            epub_filename = f"{base_name}.epub"
            dest_path = os.path.join(temp_dir, epub_filename)

            try:
                logging.info(f"Running ebook-converter: {source_path} -> {dest_path}")
                subprocess.run(
                    ['ebook-converter', source_path, dest_path],
                    capture_output=True, text=True, check=True, timeout=3600
                )
                epub_to_process_path = dest_path
            except Exception as e:
                logging.error(f"An unexpected error occurred during conversion for book_id {book_id}: {e}")
                return None, None, False

        if not epub_to_process_path or not os.path.exists(epub_to_process_path):
            logging.error(f"Could not find EPUB to process for book_id {book_id}")
            return None, None, False

        # --- Fix the EPUB ---
        logging.info(f"Processing EPUB with kindle-epub-fixer: {epub_to_process_path}")
        fixed_epub_path = fix_epub_for_kindle(epub_to_process_path, force_language=language)
        
        with open(fixed_epub_path, 'rb') as f:
            content_to_send = f.read()

        # Sanitize title and authors for use in filename
        title = safe_title(details.get('title', 'Untitled'))
        
        if filename_format == 'title':
            filename_to_send = f"{title}.epub"
        else: # Default to 'title - author'
            authors = safe_author(" & ".join(details.get('authors', [])))
            if authors:
                filename_to_send = f"{title} - {authors}.epub"
            else:
                filename_to_send = f"{title}.epub"

        return content_to_send, filename_to_send, needs_conversion

@books_bp.route('/download_book/<int:book_id>', methods=['GET'])
def download_book_api(book_id):
    details = get_calibre_book_details(book_id)
    book_title = details.get('title') if details else None
    library_type = get_provider()
    
    if g.user.force_epub_conversion:
        logging.info(f"Force EPUB conversion is ON for user {g.user.username} for book {book_id}")
        user_dict = {
            'username': g.user.username,
            'kindle_email': g.user.kindle_email,
            'send_format_priority': g.user.send_format_priority,
            'force_epub_conversion': g.user.force_epub_conversion,
            'language': g.user.language
        }
        
        language = (user_dict.get('language') or 'zh').split('_')[0]
        content, filename, needs_conversion = _get_processed_epub_for_book(book_id, user_dict, language=language)
        
        if filename == 'CONVERTER_NOT_FOUND':
            error_msg = _('This book needs to be converted to EPUB, but the `ebook-converter` tool is missing in the current environment.')
            log_activity(ActivityType.DOWNLOAD_BOOK, book_id=book_id, book_title=book_title, library_type=library_type, success=False, failure_reason=error_msg)
            return jsonify({'error': error_msg}), 412
        if content and filename:
            log_activity(ActivityType.DOWNLOAD_BOOK, book_id=book_id, book_title=book_title, library_type=library_type, success=True)
            return send_file(io.BytesIO(content), as_attachment=True, download_name=filename)
        else:
            error_msg = _('Unable to process or convert the book.')
            log_activity(ActivityType.DOWNLOAD_BOOK, book_id=book_id, book_title=book_title, library_type=library_type, success=False, failure_reason=error_msg)
            return jsonify({'error': error_msg}), 500
    else:
        # Original logic
        if not details:
            error_msg = _('Book details not found.')
            log_activity(ActivityType.DOWNLOAD_BOOK, book_id=book_id, library_type=library_type, success=False, failure_reason=error_msg)
            return jsonify({'error': error_msg}), 404

        available_formats = [f.lower() for f in details.get('formats', [])]
        priority = json.loads(g.user.send_format_priority or '[]')
        
        format_to_download = next((p_format.lower() for p_format in priority if p_format.lower() in available_formats), None)
        
        if not format_to_download:
            if available_formats:
                format_to_download = available_formats[0]
            else:
                error_msg = _('This book has no available formats.')
                log_activity(ActivityType.DOWNLOAD_BOOK, book_id=book_id, book_title=book_title, library_type=library_type, success=False, failure_reason=error_msg)
                return jsonify({'error': error_msg}), 400

        content, filename = download_calibre_book(book_id, format_to_download)
        if content:
            log_activity(ActivityType.DOWNLOAD_BOOK, book_id=book_id, book_title=book_title, library_type=library_type, success=True)
            return send_file(io.BytesIO(content), as_attachment=True, download_name=filename)
        
        error_msg = _('Unable to download the book.')
        log_activity(ActivityType.DOWNLOAD_BOOK, book_id=book_id, book_title=book_title, library_type=library_type, success=False, failure_reason=error_msg)
        return jsonify({'error': error_msg}), 404

def _send_to_kindle_logic(user_dict, book_id):
    """Core logic to send a Calibre book to a user's Kindle. Expects user as a dict."""
    if not user_dict.get('kindle_email'):
        return {'success': False, 'error': _('Please configure your Kindle email in user settings first.')}

    # Kindle always requires a processed EPUB
    language = (user_dict.get('language') or 'zh').split('_')[0]
    content_to_send, filename_to_send, needs_conversion = _get_processed_epub_for_book(book_id, user_dict, filename_format='title', language=language)

    if filename_to_send == 'CONVERTER_NOT_FOUND':
        return {'success': False, 'error': _('This book needs to be converted to EPUB, but the `ebook-converter` tool is missing. Please install it in the system PATH.'), 'code': 'CONVERTER_NOT_FOUND'}
    
    if not content_to_send:
        return {'success': False, 'error': _('Unable to get or process the EPUB file for the book.')}

    # Per Calibre's logic for Kindle, use random English text for subject and body
    subject = random_english_text(min_words_per_sentence=3, max_words_per_sentence=9, max_num_sentences=1).rstrip('.')
    body = random_english_text()
    success, message = send_email_with_config(
        user_dict['kindle_email'], 
        subject, 
        body, 
        config_manager.config, # Use the global config
        content_to_send, 
        filename_to_send
    )

    if success:
        return {'success': True, 'message': message, 'needs_conversion': needs_conversion}
    else:
        return {'success': False, 'error': message}

@books_bp.route('/send_to_kindle/<int:book_id>', methods=['POST'])
def send_to_kindle_api(book_id):
    details = get_calibre_book_details(book_id)
    book_title = details.get('title') if details else None
    library_type = get_provider()
    
    user_dict = {
        'username': g.user.username,
        'kindle_email': g.user.kindle_email,
        'send_format_priority': g.user.send_format_priority,
        'force_epub_conversion': g.user.force_epub_conversion,
        'language': g.user.language
    }
    result = _send_to_kindle_logic(user_dict, book_id)
    if result['success']:
        log_activity(ActivityType.PUSH_TO_KINDLE, book_id=book_id, book_title=book_title, library_type=library_type, success=True)
        return jsonify({'message': result['message'], 'needs_conversion': result.get('needs_conversion', False)})
    else:
        error_msg = result.get('error', _('Unknown error'))[:200]
        log_activity(ActivityType.PUSH_TO_KINDLE, book_id=book_id, book_title=book_title, library_type=library_type, success=False, failure_reason=error_msg)
        if result.get('code') == 'CONVERTER_NOT_FOUND':
            return jsonify({'error': result['error']}), 412 # Precondition Failed
        if 'Kindle 邮箱' in result.get('error', ''):
            return jsonify({'error': result['error']}), 400
        return jsonify({'error': result['error']}), 500

def _push_calibre_to_anx_logic(user_dict, book_id):
    """Core logic to push a Calibre book to a user's Anx library. Expects user as a dict."""
    book_content, book_filename = None, None

    if user_dict.get('force_epub_conversion'):
        logging.info(f"Force EPUB conversion is ON for user {user_dict['username']} for book {book_id} push to Anx.")
        language = (user_dict.get('language') or 'zh').split('_')[0]
        content, filename, _unused = _get_processed_epub_for_book(book_id, user_dict, language=language)
        if filename == 'CONVERTER_NOT_FOUND':
            return {'success': False, 'error': _('This book needs to be converted to EPUB, but the `ebook-converter` tool is missing.')}
        book_content, book_filename = content, filename
    else:
        # Original logic
        details = get_calibre_book_details(book_id)
        if not details:
            return {'success': False, 'error': _('Book details not found.')}
        available_formats = [f.lower() for f in details.get('formats', [])]
        priority_str = user_dict.get('send_format_priority') or '[]'
        priority = json.loads(priority_str)
        format_to_push = next((f for f in priority if f.lower() in available_formats), available_formats[0] if available_formats else None)

        if not format_to_push:
            return {'success': False, 'error': _('No pushable format found.')}
        
        book_content, book_filename = download_calibre_book(book_id, format_to_push)

    if not book_content:
        return {'success': False, 'error': _('Error downloading or processing the book.')}

    cover_content = get_calibre_cover_data(book_id)

    dirs = get_anx_user_dirs(user_dict['username'])
    if not dirs:
        return {'success': False, 'error': _('User directory not configured.')}

    import_dir = dirs["import"]
    os.makedirs(import_dir, exist_ok=True)

    book_file_path = os.path.join(import_dir, book_filename)
    with open(book_file_path, 'wb') as f:
        f.write(book_content)

    if cover_content:
        base_name, _unused = os.path.splitext(book_filename)
        cover_filename = f"{base_name}.jpg"
        cover_file_path = os.path.join(import_dir, cover_filename)
        with open(cover_file_path, 'wb') as f:
            f.write(cover_content)

    result = process_anx_import_folder(user_dict['username'])
    
    return {
        'success': True,
        'message': _("Book '%(filename)s' pushed. Processed: %(processed)s, Skipped: %(skipped)s.",
                     filename=book_filename,
                     processed=result.get('processed', 0),
                     skipped=result.get('skipped', 0))
    }

@books_bp.route('/push_to_anx/<int:book_id>', methods=['POST'])
def push_to_anx_api(book_id):
    details = get_calibre_book_details(book_id)
    book_title = details.get('title') if details else None
    library_type = get_provider()
    
    user_dict = {
        'username': g.user.username,
        'kindle_email': g.user.kindle_email,
        'send_format_priority': g.user.send_format_priority,
        'force_epub_conversion': g.user.force_epub_conversion,
        'language': g.user.language
    }
    result = _push_calibre_to_anx_logic(user_dict, book_id)
    if result['success']:
        log_activity(ActivityType.PUSH_TO_ANX, book_id=book_id, book_title=book_title, library_type=library_type, success=True)
        return jsonify({'message': result['message']})
    else:
        error_msg = result.get('error', _('Unknown error'))
        log_activity(ActivityType.PUSH_TO_ANX, book_id=book_id, book_title=book_title, library_type=library_type, success=False, failure_reason=error_msg)
        return jsonify({'error': error_msg}), 500

@books_bp.route('/edit_anx_metadata', methods=['POST'])
def edit_anx_metadata_api():
    data = request.get_json()
    book_id = data.pop('id', None)
    if not book_id:
        return jsonify({'error': _('Missing book ID.')}), 400

    book_title, _unused = get_anx_book_details(g.user.username, book_id)

    success, message = update_anx_book_metadata(g.user.username, book_id, data)

    if success:
        log_activity(ActivityType.EDIT_METADATA, book_id=book_id, book_title=book_title, library_type='anx', success=True, detail=json.dumps(data))
        return jsonify({'message': message})
    else:
        log_activity(ActivityType.EDIT_METADATA, book_id=book_id, book_title=book_title, library_type='anx', success=False, failure_reason=message, detail=json.dumps(data))
        return jsonify({'error': message}), 500

def _get_processed_epub_for_anx_book(id: int, username: str):
    book_details = get_anx_book_details(username, id, as_dict=True)
    if not book_details:
        return None, "BOOK_NOT_FOUND", False

    file_path = book_details.get('file_path')
    if not file_path:
        return None, "FILE_PATH_MISSING", False

    from anx_library import get_anx_user_dirs
    dirs = get_anx_user_dirs(username)
    if not dirs:
        return None, "USER_DIR_NOT_FOUND", False

    full_file_path = os.path.join(dirs['base'], 'data', file_path)
    if not os.path.exists(full_file_path):
        return None, "FILE_NOT_FOUND", False

    needs_conversion = not full_file_path.lower().endswith('.epub')

    with tempfile.TemporaryDirectory() as temp_dir:
        epub_to_process_path = None
        
        if not needs_conversion:
            epub_to_process_path = os.path.join(temp_dir, os.path.basename(full_file_path))
            shutil.copy2(full_file_path, epub_to_process_path)
        else:
            if not shutil.which('ebook-converter'):
                return None, "CONVERTER_NOT_FOUND", False

            base_name, _unused = os.path.splitext(os.path.basename(full_file_path))
            epub_filename = f"{base_name}.epub"
            dest_path = os.path.join(temp_dir, epub_filename)

            try:
                subprocess.run(
                    ['ebook-converter', full_file_path, dest_path],
                    capture_output=True, text=True, check=True, timeout=300
                )
                epub_to_process_path = dest_path
            except Exception:
                return None, "CONVERSION_FAILED", False

        if not epub_to_process_path or not os.path.exists(epub_to_process_path):
            return None, "PROCESSING_FAILED", False

        fixed_epub_path = fix_epub_for_kindle(epub_to_process_path, force_language='zh')
        
        with open(fixed_epub_path, 'rb') as f:
            content_to_send = f.read()

        final_filename = os.path.basename(fixed_epub_path)
        return content_to_send, final_filename, needs_conversion

@books_bp.route('/delete_anx_book/<int:book_id>', methods=['DELETE'])
def delete_anx_book_api(book_id):
    book_title, _unused = get_anx_book_details(g.user.username, book_id)
    
    success, message = delete_anx_book(g.user.username, book_id)
    if success:
        log_activity(ActivityType.DELETE_BOOK, book_id=book_id, book_title=book_title, library_type='anx', success=True)
        return jsonify({'message': message})
    else:
        log_activity(ActivityType.DELETE_BOOK, book_id=book_id, book_title=book_title, library_type='anx', success=False, failure_reason=message)
        return jsonify({'error': message}), 500


def _push_anx_to_calibre_logic(user_dict, book_id):
    """Core logic to push an Anx book to the Calibre library."""
    username = user_dict.get('username')
    if not username:
        return {'success': False, 'error': 'Username not found in user_dict.'}

    book_title, _unused = get_anx_book_details(username, book_id)
    if not book_title:
        return {'success': False, 'error': _('Anx book with ID %(book_id)s not found.', book_id=book_id)}
    
    book_details = get_anx_book_details(username, book_id, as_dict=True)

    file_path = book_details.get('file_path')
    if not file_path:
        return {'success': False, 'error': _('File path for book with ID %(book_id)s is missing.', book_id=book_id)}

    dirs = get_anx_user_dirs(username)
    if not dirs:
        return {'success': False, 'error': _('User directory not configured.')}

    full_file_path = os.path.join(dirs['base'], 'data', file_path)
    if not os.path.exists(full_file_path):
        return {'success': False, 'error': _('Book file not found at path: %(path)s', path=full_file_path)}

    try:
        with open(full_file_path, 'rb') as f:
            file_content = f.read()
    except IOError as e:
        return {'success': False, 'error': _('Failed to read book file: %(error)s', error=str(e))}

    filename = os.path.basename(full_file_path)
    mimetype, _unused = mimetypes.guess_type(filename)

    job_id = str(uuid.uuid4())
    library_id = config_manager.config.get('CALIBRE_DEFAULT_LIBRARY_ID', 'Calibre_Library')
    add_duplicates = config_manager.config.get('CALIBRE_ADD_DUPLICATES', False)
    add_duplicates_flag = 'y' if add_duplicates else 'n'
    encoded_filename = requests.utils.quote(filename)
    url = f"{config_manager.config['CALIBRE_URL']}/cdb/add-book/{job_id}/{add_duplicates_flag}/{encoded_filename}/{library_id}"

    try:
        headers = {'Content-Type': mimetype or 'application/octet-stream'}
        response = requests.post(url, data=file_content, auth=get_calibre_auth(), headers=headers)
        response.raise_for_status()
        res_json = response.json()

        if res_json.get("book_id"):
            uploaded_book_id = res_json["book_id"]
            try:
                uploaded_book_details = get_calibre_book_details(uploaded_book_id)
                if (uploaded_book_details and "user_metadata" in uploaded_book_details and
                        "#library" in uploaded_book_details["user_metadata"]):
                    update_payload = {"changes": {"#library": username}}
                    update_url = f"{config_manager.config['CALIBRE_URL']}/cdb/set-fields/{uploaded_book_id}/{library_id}"
                    update_response = requests.post(update_url, json=update_payload, auth=get_calibre_auth())
                    update_response.raise_for_status()
                    logging.info(f"Successfully updated #library for book {uploaded_book_id}")
            except Exception as e:
                logging.error(f"Failed to update #library for book {uploaded_book_id}: {e}")
                return {
                    'success': True,
                    'message': _("Book '%(title)s' uploaded successfully, ID: %(book_id)s (but failed to update source).",
                                 title=res_json.get('title'), book_id=uploaded_book_id)
                }

            return {
                'success': True,
                'message': _("Book '%(title)s' uploaded successfully, ID: %(book_id)s.",
                             title=res_json.get('title'), book_id=uploaded_book_id)
            }
        else:
            return {
                'success': False,
                'error': _("Upload failed, book may already exist."),
                'details': res_json.get("duplicates"),
                'code': 409
            }

    except requests.exceptions.HTTPError as e:
        error_message = _("Calibre server returned an error: %(code)s - %(text)s",
                          code=e.response.status_code, text=e.response.text)
        return {'success': False, 'error': error_message, 'code': 500}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': _("Error connecting to Calibre server: %(error)s", error=e), 'code': 500}


import hashlib
import posixpath
from utils.ebook_utils import process_uploaded_ebook
from utils.text import safe_title, safe_author, sanitize_filename
from anx_library import add_book_to_anx_db

def _upload_to_anx_logic(user_dict, uploaded_files):
    """Core logic to upload books to a user's Anx library."""
    username = user_dict.get('username')
    if not username:
        return {'success': False, 'error': _('Username not found in user_dict.')}

    if not uploaded_files:
        return {'success': False, 'error': _('No files were uploaded.')}

    dirs = get_anx_user_dirs(username)
    if not dirs:
        return {'success': False, 'error': _('User directory not configured.')}

    # Since the frontend sends one file at a time, we process the first one.
    file = uploaded_files[0]
    if not file.filename:
        return {'success': False, 'error': _('No files selected for uploading.')}

    original_filename = os.path.basename(file.filename)
    _unused, ext = os.path.splitext(original_filename)
    temp_filepath = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
            file.save(temp_file.name)
            temp_filepath = temp_file.name

        # Force EPUB conversion if the user setting is enabled
        if user_dict.get('force_epub_conversion') and ext.lower() != '.epub':
            if not shutil.which('ebook-converter'):
                return {'success': False, 'error': _('`ebook-converter` tool is missing, cannot convert file.'), 'code': 412}

            converted_epub_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.epub")
            try:
                result = subprocess.run(
                    ['ebook-converter', temp_filepath, converted_epub_path],
                    capture_output=True, text=True, check=True, timeout=300
                )
            except subprocess.CalledProcessError as e:
                error_details = e.stderr or e.stdout or str(e)
                return {'success': False, 'error': _('Conversion failed: %(details)s', details=error_details), 'code': 500}
            
            os.unlink(temp_filepath)
            temp_filepath = converted_epub_path
            ext = '.epub'

        metadata = process_uploaded_ebook(temp_filepath, original_filename=original_filename)
        
        title = safe_title(metadata['title'])
        author = safe_author(metadata['author'])
        
        base_filename = f"{title} - {author}"
        
        new_book_filename = f"{base_filename}{ext}"
        new_cover_filename = f"{base_filename}.jpg"

        # Create subdirectories
        file_dir = dirs['file']
        cover_dir = dirs['cover']
        os.makedirs(file_dir, exist_ok=True)
        os.makedirs(cover_dir, exist_ok=True)

        book_dest_path = os.path.join(file_dir, new_book_filename)
        cover_dest_path = os.path.join(cover_dir, new_cover_filename)

        # Calculate MD5 before moving
        with open(temp_filepath, 'rb') as f:
            file_md5 = hashlib.md5(f.read()).hexdigest()

        # Prepare data for DB
        book_data_for_db = {
            'title': title,
            'author': author,
            'description': metadata.get('comments', ''),
            'file_md5': file_md5
        }
        
        # Use POSIX paths for DB
        db_file_path = posixpath.join('file', new_book_filename)
        db_cover_path = posixpath.join('cover', new_cover_filename)

        success, status = add_book_to_anx_db(username, book_data_for_db, db_file_path, db_cover_path)

        if status == "DUPLICATE":
            os.unlink(temp_filepath) # Clean up temp file
            return {'success': True, 'message': _("Book '%(title)s' already exists in the library.", title=title)}
        
        # If reactivated or new, move/save the files
        shutil.move(temp_filepath, book_dest_path)
        if metadata['cover']:
            with open(cover_dest_path, 'wb') as f:
                f.write(metadata['cover'])

        if status == "REACTIVATED":
            return {'success': True, 'message': _("Reactivated previously deleted book '%(title)s'.", title=title)}
        
        return {'success': True, 'message': _("Book '%(title)s' uploaded successfully.", title=title)}

    except Exception as e:
        logging.error(f"Failed to process uploaded file {original_filename} for user {username}: {e}")
        if temp_filepath and os.path.exists(temp_filepath):
            os.unlink(temp_filepath)
        return {'success': False, 'error': _("Failed to process '%(filename)s': %(error)s", filename=original_filename, error=str(e)), 'code': 500}


@books_bp.route('/upload_to_anx', methods=['POST'])
def upload_to_anx_api():
    # Permission check for normal users
    if config_manager.config.get('DISABLE_NORMAL_USER_UPLOAD') and g.user.role == 'user':
        error_msg = _('You do not have permission to upload books.')
        log_activity(ActivityType.UPLOAD_BOOK, library_type='anx', success=False, failure_reason=error_msg)
        return jsonify([{'success': False, 'error': error_msg}]), 403

    if 'books' not in request.files:
        return jsonify([{'success': False, 'error': _('No file part in the request.')}]), 400

    uploaded_files = request.files.getlist('books')
    if not uploaded_files or all(f.filename == '' for f in uploaded_files):
        return jsonify([{'success': False, 'error': _('No files selected for uploading.')}]), 400

    # We process one file at a time as per the frontend logic, but the logic can handle multiple
    user_dict = {
        'username': g.user.username,
        'force_epub_conversion': g.user.force_epub_conversion
    }
    result = _upload_to_anx_logic(user_dict, uploaded_files)

    # The frontend expects a list of results, even for a single file.
    final_result = {
        'success': result['success'],
        'message': result.get('message'),
        'error': result.get('error')
    }

    if result['success']:
        log_activity(ActivityType.UPLOAD_BOOK, library_type='anx', success=True, detail=result.get('message'))
        return jsonify([final_result])
    else:
        log_activity(ActivityType.UPLOAD_BOOK, library_type='anx', success=False, failure_reason=result.get('error'))
        status_code = result.get('code', 500)
        return jsonify([final_result]), status_code


@books_bp.route('/push_anx_to_calibre/<int:book_id>', methods=['POST'])
def push_anx_to_calibre_api(book_id):
    book_details = get_anx_book_details(g.user.username, book_id, as_dict=True)
    book_title = book_details.get('title') if book_details else None

    # Permission check for normal users
    if config_manager.config.get('DISABLE_NORMAL_USER_UPLOAD') and g.user.role == 'user':
        error_msg = _('You do not have permission to upload books.')
        log_activity(ActivityType.PUSH_ANX_TO_CALIBRE, book_id=book_id, book_title=book_title, library_type='anx', success=False, failure_reason=error_msg)
        return jsonify({'error': error_msg}), 403

    user_dict = {'username': g.user.username}
    result = _push_anx_to_calibre_logic(user_dict, book_id)
    
    if result['success']:
        log_activity(ActivityType.PUSH_ANX_TO_CALIBRE, book_id=book_id, book_title=book_title, library_type='anx', success=True, detail=result.get('message'))
        return jsonify({'message': result['message']})
    else:
        error_msg = result.get('error', _('Unknown error'))
        log_activity(ActivityType.PUSH_ANX_TO_CALIBRE, book_id=book_id, book_title=book_title, library_type='anx', success=False, failure_reason=error_msg, detail=json.dumps(result.get('details')))
        status_code = result.get('code', 500)
        error_payload = {'error': error_msg}
        if 'details' in result:
            error_payload['details'] = result['details']
        return jsonify(error_payload), status_code