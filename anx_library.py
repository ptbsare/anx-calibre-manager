import os
import sqlite3
import hashlib
import re
import shutil
from contextlib import closing
from datetime import datetime
from config_manager import config
from anx_db_schema import ANX_DB_SCHEMA
from utils.ebook_utils import extract_ebook_metadata, generate_cover_image
from utils.text import safe_title, safe_author

def initialize_anx_user_data(username):
    """Creates the necessary directory structure and initializes an empty Anx database for a new user."""
    dirs = get_anx_user_dirs(username)
    if not dirs:
        print(f"Could not get user directories for {username}. WEBDAV_ROOT might be missing.")
        return False, f"无法为用户 {username} 获取目录结构。"

    try:
        # Create all necessary directories
        # The full structure is /webdav/<user>/anx/data/file, etc.
        os.makedirs(dirs["file"], exist_ok=True)
        os.makedirs(dirs["cover"], exist_ok=True)
        os.makedirs(dirs["import"], exist_ok=True)
        os.makedirs(dirs["already_in"], exist_ok=True)

        # Initialize the database only if it doesn't exist
        if not os.path.exists(dirs["db_path"]):
            with closing(sqlite3.connect(dirs["db_path"])) as db:
                cursor = db.cursor()
                cursor.executescript(ANX_DB_SCHEMA)
                current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("""
                    INSERT INTO tb_groups (id, name, parent_id, is_deleted, create_time, update_time)
                    VALUES (0, 'Root', NULL, 0, ?, ?)
                """, (current_time, current_time))
                db.commit()
        
        return True, "用户 Anx 数据目录和数据库已成功初始化。"
    except Exception as e:
        print(f"Error initializing Anx data for user {username}: {e}")
        return False, f"初始化用户 Anx 数据时出错: {e}"

def get_anx_user_dirs(username):
    """Gets all the relevant directory paths for a user's Anx library."""
    webdav_root = config.get("WEBDAV_ROOT")
    if not webdav_root or not username:
        return None
    safe_username = os.path.basename(username)
    user_root = os.path.join(webdav_root, safe_username)
    base_dir = os.path.join(user_root, 'anx')
    
    return {
        "user_root": user_root,
        "base": base_dir,
        "db_path": os.path.join(base_dir, "database7.db"),
        "import": os.path.join(base_dir, "import"),
        "workspace": os.path.join(base_dir, "data"),
        "file": os.path.join(base_dir, "data", "file"),
        "cover": os.path.join(base_dir, "data", "cover"),
        "already_in": os.path.join(base_dir, "alreadyin"),
    }

def get_anx_books(username):
    """Fetches all non-deleted books for a user from their Anx database."""
    dirs = get_anx_user_dirs(username)
    db_path = dirs["db_path"] if dirs else None
    
    if not db_path or not os.path.exists(db_path):
        print(f"ANX DB not found for user {username} at {db_path}")
        return []

    books = []
    try:
        with closing(sqlite3.connect(db_path)) as db:
            db.row_factory = sqlite3.Row
            cursor = db.cursor()
            query = """
                SELECT
                    b.*,
                    COALESCE(SUM(rt.reading_time), 0) as total_reading_time,
                    COALESCE(COUNT(DISTINCT n.id), 0) as note_count
                FROM
                    tb_books b
                LEFT JOIN
                    tb_reading_time rt ON b.id = rt.book_id
                LEFT JOIN
                    tb_notes n ON b.id = n.book_id
                WHERE
                    b.is_deleted = 0
                GROUP BY
                    b.id
                ORDER BY
                    b.update_time DESC
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            for row in rows:
                books.append(dict(row))
    except Exception as e:
        print(f"Error reading Anx database for user {username}: {e}")
        return []
    
    return books

def get_anx_book_path(username, book_id):
    """根据 book_id 获取 Anx 书籍的完整文件路径"""
    dirs = get_anx_user_dirs(username)
    if not dirs or not os.path.exists(dirs["db_path"]):
        raise FileNotFoundError("Anx database not found.")
    
    with closing(sqlite3.connect(dirs["db_path"])) as db:
        db.row_factory = sqlite3.Row
        book_row = db.execute("SELECT file_path FROM tb_books WHERE id = ?", (book_id,)).fetchone()
        if not book_row or not book_row['file_path']:
            raise FileNotFoundError(f"Anx book file with ID {book_id} not found.")
        
        return os.path.join(dirs["workspace"], book_row['file_path'])

def get_anx_book_details(username, book_id, as_dict=False):
    """
    Fetches the details for a single Anx book by its ID.
    
    Args:
        username: 用户名
        book_id: 书籍ID
        as_dict: 如果为True，返回完整的字典；如果为False，返回(title, author)元组
    
    Returns:
        如果 as_dict=True: 返回完整的书籍字典，未找到返回 None
        如果 as_dict=False: 返回 (title, author) 元组，未找到返回 (None, None)
    """
    all_books = get_anx_books(username)
    for book in all_books:
        if book['id'] == book_id:
            if as_dict:
                return book
            else:
                return book.get('title'), book.get('author')
    
    if as_dict:
        return None
    else:
        return None, None

def _calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def process_anx_import_folder(username):
    """Processes files in a user's Anx import folder and adds them to the database."""
    dirs = get_anx_user_dirs(username)
    if not dirs:
        return {"error": "User directories not configured."}

    for path in [dirs["import"], dirs["file"], dirs["cover"], dirs["already_in"]]:
        os.makedirs(path, exist_ok=True)

    processed_count = 0
    skipped_count = 0
    
    # Classify files first to avoid premature moves
    all_files = [f for f in os.listdir(dirs["import"]) if os.path.isfile(os.path.join(dirs["import"], f))]
    
    ebook_extensions = {"epub", "mobi", "azw3", "pdf", "txt"}
    cover_extensions = {"jpg", "jpeg", "png", "gif"}
    
    ebook_files = {}
    cover_files = {}
    other_files = []

    for filename in all_files:
        base_name, extension = os.path.splitext(filename)
        ext_lower = extension[1:].lower()
        
        if ext_lower in ebook_extensions:
            ebook_files[base_name] = filename
        elif ext_lower in cover_extensions:
            cover_files[base_name] = filename
        else:
            other_files.append(filename)

    # Process ebooks and their matching covers
    for base_name, ebook_filename in ebook_files.items():
        file_path = os.path.join(dirs["import"], ebook_filename)
        
        # --- Optimized Metadata Handling ---
        # 1. Extract metadata from file ONCE.
        metadata = extract_ebook_metadata(file_path)

        # 2. Determine title and author, with filename having priority.
        title, author = base_name, "Unknown Author"
        match = re.match(r'^(.*) - (.*)$', base_name)
        if match:
            title, author = match.groups()
        elif metadata:  # Fallback to extracted metadata if filename is not standard
            if metadata.get('title') and metadata['title'] != 'Unknown Title':
                title = safe_title(metadata['title'])
            if metadata.get('author') and metadata['author'] != 'Unknown Author':
                author = safe_author(metadata['author'])
        
        # 3. Calculate MD5
        file_md5 = _calculate_md5(file_path)

        with closing(sqlite3.connect(dirs["db_path"])) as db:
            cursor = db.cursor()
            cursor.execute("SELECT id, is_deleted FROM tb_books WHERE file_md5 = ?", (file_md5,))
            existing = cursor.fetchone()

            cover_filename = cover_files.pop(base_name, None)
            cover_relative_path = ""

            # --- Book Processing (Reactivate or Add New) ---
            if existing:
                existing_id, is_deleted = existing
                if is_deleted == 1: # Reactivate soft-deleted book
                    print(f"Reactivating deleted book with MD5: {file_md5}")
                    
                    dest_file_path = os.path.join(dirs["file"], ebook_filename)
                    shutil.move(file_path, dest_file_path)
                    file_relative_path = 'file/' + ebook_filename

                    # --- Cover Handling for Reactivation ---
                    if cover_filename:
                        cover_path = os.path.join(dirs["import"], cover_filename)
                        dest_cover_path = os.path.join(dirs["cover"], cover_filename)
                        shutil.move(cover_path, dest_cover_path)
                        cover_relative_path = 'cover/' + cover_filename
                    else:
                        cover_data = metadata.get('cover') if metadata else None
                        if not cover_data:
                            cover_data = generate_cover_image(title, author)
                        if cover_data:
                            new_cover_filename = f"{base_name}.jpg"
                            dest_cover_path = os.path.join(dirs["cover"], new_cover_filename)
                            with open(dest_cover_path, 'wb') as f: f.write(cover_data)
                            cover_relative_path = 'cover/' + new_cover_filename
                    
                    current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                    cursor.execute("""
                        UPDATE tb_books
                        SET is_deleted = 0, update_time = ?, file_path = ?, cover_path = ?, title = ?, author = ?
                        WHERE id = ?
                    """, (current_time, file_relative_path, cover_relative_path, title, author, existing_id))
                    db.commit()
                    processed_count += 1
                else: # True duplicate
                    shutil.move(file_path, os.path.join(dirs["already_in"], ebook_filename))
                    if cover_filename:
                        shutil.move(os.path.join(dirs["import"], cover_filename), os.path.join(dirs["already_in"], cover_filename))
                    skipped_count += 1
                continue

            # --- Add New Book ---
            dest_file_path = os.path.join(dirs["file"], ebook_filename)
            shutil.move(file_path, dest_file_path)
            file_relative_path = 'file/' + ebook_filename

            # --- Cover Handling for New Book ---
            if cover_filename:
                cover_path = os.path.join(dirs["import"], cover_filename)
                dest_cover_path = os.path.join(dirs["cover"], cover_filename)
                shutil.move(cover_path, dest_cover_path)
                cover_relative_path = 'cover/' + cover_filename
            else:
                cover_data = metadata.get('cover') if metadata else None
                if not cover_data:
                    cover_data = generate_cover_image(title, author)
                if cover_data:
                    new_cover_filename = f"{base_name}.jpg"
                    dest_cover_path = os.path.join(dirs["cover"], new_cover_filename)
                    with open(dest_cover_path, 'wb') as f: f.write(cover_data)
                    cover_relative_path = 'cover/' + new_cover_filename
            
            current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            cursor.execute("""
                INSERT INTO tb_books (
                    title, author, cover_path, file_path, file_md5, create_time, update_time,
                    is_deleted, last_read_position, reading_percentage, rating, group_id, description
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                title, author, cover_relative_path, file_relative_path, file_md5,
                current_time, current_time, 0, '', 0.0, 0.0, 0, ''
            ))
            db.commit()
            processed_count += 1

    # Move remaining files (unmatched covers and other files) to already_in
    remaining_files = other_files + list(cover_files.values())
    for filename in remaining_files:
        file_path = os.path.join(dirs["import"], filename)
        if os.path.exists(file_path): # Check if it wasn't moved already (e.g. as a duplicate's cover)
            shutil.move(file_path, os.path.join(dirs["already_in"], filename))
            
    return {"processed": processed_count, "skipped": skipped_count}


def update_anx_book_metadata(username, book_id, data):
    """Updates the metadata for a specific book in a user's Anx database."""
    dirs = get_anx_user_dirs(username)
    db_path = dirs["db_path"] if dirs else None
    
    if not db_path or not os.path.exists(db_path):
        return False, "Anx database not found."

    allowed_fields = ['title', 'author', 'rating', 'description']
    update_data = {key: data[key] for key in data if key in allowed_fields}
    
    if not update_data:
        return False, "No valid data provided for update."

    update_data['update_time'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
    values = list(update_data.values())
    values.append(book_id)
    query = f"UPDATE tb_books SET {set_clause} WHERE id = ?"

    try:
        with closing(sqlite3.connect(db_path)) as db:
            cursor = db.cursor()
            cursor.execute(query, tuple(values))
            db.commit()
            if cursor.rowcount == 0:
                return False, f"Book with ID {book_id} not found."
            return True, "Metadata updated successfully."
    except Exception as e:
        print(f"Error updating Anx database for user {username}: {e}")
        return False, f"Error updating database: {e}"

def delete_anx_book(username, book_id):
    """Deletes a book from a user's Anx library by marking it as deleted and removing files."""
    dirs = get_anx_user_dirs(username)
    if not dirs or not os.path.exists(dirs["db_path"]):
        return False, "Anx database not found."

    try:
        with closing(sqlite3.connect(dirs["db_path"])) as db:
            db.row_factory = sqlite3.Row
            cursor = db.cursor()
            
            cursor.execute("SELECT file_path, cover_path FROM tb_books WHERE id = ?", (book_id,))
            book_files = cursor.fetchone()
            
            if not book_files:
                return False, f"Book with ID {book_id} not found."

            current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            cursor.execute("UPDATE tb_books SET is_deleted = 1, update_time = ? WHERE id = ?", (current_time, book_id))
            db.commit()

            if book_files['file_path']:
                file_to_delete = os.path.join(dirs["base"], 'data', book_files['file_path'])
                if os.path.exists(file_to_delete):
                    os.remove(file_to_delete)
            
            if book_files['cover_path']:
                cover_to_delete = os.path.join(dirs["base"], 'data', book_files['cover_path'])
                if os.path.exists(cover_to_delete):
                    os.remove(cover_to_delete)

            return True, "Book deleted successfully."
    except Exception as e:
        print(f"Error deleting book {book_id} for user {username}: {e}")
        return False, f"Error deleting book: {e}"

def add_book_to_anx_db(username, book_data, new_file_path, new_cover_path):
    """
    Adds or reactivates a single, processed book in the user's Anx database.
    Handles duplicate checks and reactivates soft-deleted books.
    """
    dirs = get_anx_user_dirs(username)
    if not dirs or not os.path.exists(dirs["db_path"]):
        raise FileNotFoundError("Anx database not found.")

    with closing(sqlite3.connect(dirs["db_path"])) as db:
        cursor = db.cursor()
        
        cursor.execute("SELECT id, is_deleted FROM tb_books WHERE file_md5 = ?", (book_data['file_md5'],))
        existing = cursor.fetchone()
        
        current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        if existing:
            existing_id, is_deleted = existing
            if is_deleted == 1:
                # Reactivate the book
                cursor.execute("""
                    UPDATE tb_books
                    SET is_deleted = 0,
                        update_time = ?,
                        file_path = ?,
                        cover_path = ?,
                        title = ?,
                        author = ?,
                        description = ?
                    WHERE id = ?
                """, (
                    current_time,
                    new_file_path,
                    new_cover_path,
                    book_data.get('title', 'Unknown Title'),
                    book_data.get('author', 'Unknown Author'),
                    book_data.get('description', ''),
                    existing_id
                ))
                db.commit()
                return True, "REACTIVATED"
            else:
                # It's a true duplicate
                return False, "DUPLICATE"

        # Insert new book
        cursor.execute("""
            INSERT INTO tb_books (
                title, author, cover_path, file_path, file_md5, create_time, update_time,
                is_deleted, last_read_position, reading_percentage, rating, group_id, description
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            book_data.get('title', 'Unknown Title'),
            book_data.get('author', 'Unknown Author'),
            new_cover_path,
            new_file_path,
            book_data.get('file_md5', ''),
            current_time,
            current_time,
            0, '', 0.0, 0.0, 0,
            book_data.get('description', '')
        ))
        db.commit()
    
    return True, "SUCCESS"
