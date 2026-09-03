import json
import requests
import uuid
import logging
from functools import lru_cache
from urllib.parse import quote
from flask import Blueprint, request, jsonify, g, send_from_directory
from flask_babel import gettext as _
from contextlib import closing
import config_manager
from utils.auth import get_calibre_auth
from utils.library_provider import library_request, get_provider
from utils.text import safe_title, safe_author
from utils.decorators import maintainer_required_api
from utils.activity_logger import log_activity, ActivityType

calibre_bp = Blueprint('calibre', __name__, url_prefix='/api')

@calibre_bp.route('/upload_to_calibre', methods=['POST'])
def upload_to_calibre_api():
    # Permission check for normal users
    if config_manager.config.get('DISABLE_NORMAL_USER_UPLOAD') and g.user.role == 'user':
        error_msg = _('You do not have permission to upload books.')
        log_activity(ActivityType.UPLOAD_BOOK, library_type='calibre', success=False, failure_reason=error_msg)
        return jsonify({'error': error_msg}), 403

    if 'books' not in request.files:
        return jsonify({'error': _('No file part.')}), 400
    
    files = request.files.getlist('books')
    if not files or files[0].filename == '':
        return jsonify({'error': _('No selected file.')}), 400

    results = []
    for file in files:
        if file:
            filename = file.filename
            
            job_id = str(uuid.uuid4())
            library_id = config_manager.config.get('CALIBRE_DEFAULT_LIBRARY_ID', 'Calibre_Library')
            add_duplicates = config_manager.config.get('CALIBRE_ADD_DUPLICATES', False)
            add_duplicates_flag = 'y' if add_duplicates else 'n'
            encoded_filename = requests.utils.quote(filename)
            url = f"{config_manager.config['CALIBRE_URL']}/cdb/add-book/{job_id}/{add_duplicates_flag}/{encoded_filename}/{library_id}"
            
            try:
                headers = {'Content-Type': file.mimetype} if file.mimetype else {}
                
                # We must read the file content into memory before passing it to requests,
                # as the file object will be closed after the first iteration.
                file.seek(0)
                file_content = file.read()
                
                response = requests.post(url, data=file_content, auth=get_calibre_auth(), headers=headers)
                response.raise_for_status()
                
                res_json = response.json()
                if res_json.get("book_id"):
                    book_id = res_json["book_id"]
                    book_title = res_json.get('title', filename)
                    log_activity(ActivityType.UPLOAD_BOOK, book_id=book_id, book_title=book_title, library_type='calibre', success=True)

                    # Try to update #library tag, but don't fail the entire request if this part fails
                    try:
                        book_details = get_calibre_book_details(book_id)
                        if (book_details and "user_metadata" in book_details and "#library" in book_details["user_metadata"]):
                            update_payload = {"changes": {"#library": g.user.username}}
                            update_url = f"{config_manager.config['CALIBRE_URL']}/cdb/set-fields/{book_id}/{library_id}"
                            update_response = requests.post(update_url, json=update_payload, auth=get_calibre_auth())
                            update_response.raise_for_status()
                            logging.info(f"Successfully updated #library for book {book_id}")
                    except Exception as e:
                        logging.error(f"Failed to update #library for book {book_id}: {e}")
                    
                    results.append({"success": True, "filename": filename, "message": _("Book '%(title)s' uploaded successfully, ID: %(book_id)s.", title=book_title, book_id=book_id)})
                else:
                    error_msg = _("Upload failed, book may already exist.")
                    log_activity(ActivityType.UPLOAD_BOOK, book_title=filename, library_type='calibre', success=False, failure_reason=error_msg, detail=json.dumps(res_json.get("duplicates")))
                    results.append({"success": False, "filename": filename, "error": error_msg, "details": res_json.get("duplicates")})
            
            except requests.exceptions.HTTPError as e:
                error_message = _("Calibre server returned an error: %(code)s - %(text)s", code=e.response.status_code, text=e.response.text)
                log_activity(ActivityType.UPLOAD_BOOK, book_title=filename, library_type='calibre', success=False, failure_reason=error_message)
                results.append({"success": False, "filename": filename, "error": error_message})
            except requests.exceptions.RequestException as e:
                error_message = _("Error connecting to Calibre server: %(error)s", error=e)
                log_activity(ActivityType.UPLOAD_BOOK, book_title=filename, library_type='calibre', success=False, failure_reason=error_message)
                results.append({"success": False, "filename": filename, "error": error_message})

    return jsonify(results)

@calibre_bp.route('/update_calibre_book/<int:book_id>', methods=['POST'])
def update_calibre_book_api(book_id):
    book_details = get_calibre_book_details(book_id)
    book_title = book_details.get('title') if book_details else None

    if not g.user.is_maintainer:
        if not book_details:
            error_msg = _('Book not found')
            log_activity(ActivityType.EDIT_METADATA, book_id=book_id, library_type='calibre', success=False, failure_reason=error_msg)
            return jsonify({'error': error_msg}), 404
        
        library_field = book_details.get('user_metadata', {}).get('#library', {})
        uploader = library_field.get('#value#', '') if library_field else ''

        if uploader != g.user.username:
            error_msg = _('You do not have permission to edit this book.')
            log_activity(ActivityType.EDIT_METADATA, book_id=book_id, book_title=book_title, library_type='calibre', success=False, failure_reason=error_msg)
            return jsonify({'error': error_msg}), 403

    data = request.get_json()
    
    # Prepare the 'changes' dictionary
    changes = {
        'title': data.get('title'),
        'authors': data.get('authors'),
        'rating': data.get('rating'),
        'comments': data.get('comments'),
        'publisher': data.get('publisher'),
        'tags': data.get('tags'),
        '#library': data.get('#library'),
        '#readdate': data.get('#readdate'),
        'pubdate': data.get('pubdate')
    }
    
    # Filter out any keys with None values, but keep empty strings as they represent a deliberate clearing of a field.
    changes = {k: v for k, v in changes.items() if v is not None}

    # If authors is a string, split it into a list as required by Calibre
    if 'authors' in changes and isinstance(changes['authors'], str):
        changes['authors'] = [a.strip() for a in changes['authors'].split('&')]

    # Handle date fields: Calibre expects a special string for undefined/cleared dates.
    UNDEFINED_DATE_ISO = '0101-01-01T00:00:00+00:00'
    for date_field in ['pubdate', '#readdate']:
        if date_field in changes and changes[date_field] == '':
            changes[date_field] = UNDEFINED_DATE_ISO

    if not changes:
        return jsonify({'error': _('No fields provided to update.')}), 400

    payload = {'changes': changes}
    library_id = config_manager.config.get('CALIBRE_DEFAULT_LIBRARY_ID', 'Calibre_Library')
    url = f"{config_manager.config['CALIBRE_URL']}/cdb/set-fields/{book_id}/{library_id}"
    
    try:
        response = requests.post(url, json=payload, auth=get_calibre_auth())
        response.raise_for_status()
        
        try:
            result = response.json()
            # The cdb endpoint returns the updated metadata for the book
            if str(book_id) in result:
                log_activity(ActivityType.EDIT_METADATA, book_id=book_id, book_title=book_title, library_type='calibre', success=True, detail=json.dumps(changes))
                return jsonify({'message': _('Metadata updated successfully.'), 'updated_metadata': result[str(book_id)]})
            else:
                error_msg = _('Calibre returned an unknown response.')
                log_activity(ActivityType.EDIT_METADATA, book_id=book_id, book_title=book_title, library_type='calibre', success=False, failure_reason=error_msg, detail=json.dumps(result))
                return jsonify({'error': error_msg, 'details': result}), 500
        except json.JSONDecodeError:
            error_msg = _('Calibre returned an invalid JSON response: %(text)s', text=response.text)
            log_activity(ActivityType.EDIT_METADATA, book_id=book_id, book_title=book_title, library_type='calibre', success=False, failure_reason=error_msg)
            return jsonify({'error': error_msg}), 500
                
    except requests.exceptions.HTTPError as e:
        error_message = _('Error connecting to Calibre server: %(code)s %(reason)s', code=e.response.status_code, reason=e.response.reason)
        log_activity(ActivityType.EDIT_METADATA, book_id=book_id, book_title=book_title, library_type='calibre', success=False, failure_reason=error_message)
        return jsonify({'error': error_message, 'details': e.response.text}), 500
    except requests.exceptions.RequestException as e:
        error_message = _('Error connecting to Calibre server: %(error)s', error=e)
        log_activity(ActivityType.EDIT_METADATA, book_id=book_id, book_title=book_title, library_type='calibre', success=False, failure_reason=error_message)
        return jsonify({'error': error_message}), 500

# --- Completions API ---
@lru_cache(maxsize=16)
def get_all_items_for_field(library_id, field):
    """
    Fetches all items for a given field from the Calibre server.
    Results are cached to avoid repeated requests for the same field.
    """
    encoded_field = quote(field)
    url = f"{config_manager.config['CALIBRE_URL']}/interface-data/field-names/{encoded_field}?library_id={library_id}"
    try:
        response = requests.get(url, auth=get_calibre_auth())
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Could not fetch completions for field '{field}': {e}")
        return []

@calibre_bp.route('/calibre/completions', methods=['GET'])
@maintainer_required_api
def calibre_completions_api():
    field = request.args.get('field')
    query = request.args.get('query', '').lower()
    
    if not field:
        return jsonify({'error': _('Field parameter is required.')}), 400

    supported_fields = ['authors', 'publisher', 'tags', '#library']
    if field not in supported_fields:
        return jsonify({'error': _("Completions not supported for field: %(field)s", field=field)}), 400

    library_id = config_manager.config.get('CALIBRE_DEFAULT_LIBRARY_ID', 'Calibre_Library')
    
    all_items = get_all_items_for_field(library_id, field)
    
    if not query:
        # Return a small subset if query is empty
        return jsonify(all_items[:20])

    filtered_items = [item for item in all_items if query in item.lower()]
    
    return jsonify(filtered_items[:20]) # Return max 20 results

@calibre_bp.route('/download_koreader_plugin', methods=['GET'])
def download_koreader_plugin():
    # The zip file is created in the static directory by the Dockerfile
    return send_from_directory('static', 'anx-calibre-manager-koreader-plugin.zip', as_attachment=True)

def get_calibre_book_details(book_id):
    try:
        response = library_request('GET', f"/ajax/book/{book_id}?fields=all")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting book details for {book_id}: {e}")
        return None

def download_calibre_book(book_id, download_format='mobi'):
    details = get_calibre_book_details(book_id)
    if not details: return None, None
    title = safe_title(details.get('title', 'Unknown Title'))
    authors = safe_author(" & ".join(details.get('authors', ['Unknown Author'])))
    if authors:
        filename = f"{title} - {authors}.{download_format}"
    else:
        filename = f"{title}.{download_format}"
    
    try:
        response = library_request('GET', f"/get/{download_format.lower()}/{book_id}", stream=True)
        response.raise_for_status()
        return response.content, filename
    except requests.exceptions.RequestException as e:
        from utils.library_provider import get_base_url
        url = f"{get_base_url()}/get/{download_format.lower()}/{book_id}"
        print(f"Error downloading book {book_id} in format {download_format} from URL {url}: {e}")
        return None, None