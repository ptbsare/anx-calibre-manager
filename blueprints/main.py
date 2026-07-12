import math
import re
import requests
import io
import os
from urllib.parse import urlencode
from flask import Blueprint, render_template, request, g, redirect, url_for, send_from_directory, send_file, make_response
from flask_babel import gettext as _
from requests.auth import HTTPDigestAuth
import json

import config_manager
from database import get_db
from anx_library import get_anx_books
from utils.text import safe_title, safe_author
from utils.auth import get_calibre_auth
from utils.covers import get_calibre_cover_data
from utils.decorators import login_required
from utils.library_provider import library_request, get_base_url, get_provider

main_bp = Blueprint('main', __name__)

def get_calibre_books(search_query="", page=1, page_size=20):
    config = config_manager.config
    base_url = get_base_url()
    full_url = base_url
    try:
        library_id = config.get('CALIBRE_DEFAULT_LIBRARY_ID', 'Calibre_Library')
        offset = (page - 1) * page_size
        search_params = { 'query': search_query, 'num': page_size, 'offset': offset, 'library_id': library_id, 'sort': 'id', 'sort_order': 'desc' }
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        full_url = f"{base_url}/ajax/search?{urlencode(search_params)}"

        search_response = library_request('GET', '/ajax/search', params=search_params, headers=headers)
        search_response.raise_for_status()
        search_data = search_response.json()
        book_ids = search_data.get('book_ids', [])
        total_books = search_data.get('total_num', 0)
        if not book_ids: return [], 0, None
        books_data = {}
        chunk_size = 100
        for i in range(0, len(book_ids), chunk_size):
            chunk = book_ids[i:i + chunk_size]
            if not chunk: continue
            requested_fields = 'all'
            books_params = {'ids': ",".join(map(str, chunk)), 'library_id': library_id, 'fields': requested_fields}
            books_response = library_request('GET', '/ajax/books', params=books_params, headers=headers)
            books_response.raise_for_status()
            books_data.update(books_response.json())

        books = []
        for bid in book_ids:
            bid_str = str(bid)
            if bid_str in books_data:
                book_dict = books_data[bid_str]
                if book_dict:
                    book_dict['id'] = bid
                    books.append(book_dict)
        
        def format_bytes(size):
            if not size or size == 0: return "0B"
            power = 1024
            n = 0
            power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
            while size >= power and n < len(power_labels) - 1:
                size /= power
                n += 1
            return f"{size:.1f} {power_labels[n]}"

        for book in books:
            formats_with_sizes = []
            format_metadata = book.get('format_metadata', {})
            if isinstance(format_metadata, dict):
                for fmt, details in format_metadata.items():
                    size = details.get('size', 0)
                    formats_with_sizes.append(f"{fmt.upper()} ({format_bytes(size)})")
            
            book['formats_with_sizes'] = formats_with_sizes
            book['formats'] = list(format_metadata.keys()) if isinstance(format_metadata, dict) else []

        return books, total_books, None
    except requests.exceptions.ConnectionError as e:
        print(f"Error getting Calibre books: {e}")
        return [], 0, {'code': 'CONNECTION_ERROR', 'message': str(e), 'calibre_url': full_url}
    except requests.exceptions.HTTPError as e:
        print(f"Error getting Calibre books: {e}")
        error_info = {'message': str(e), 'calibre_url': e.response.url}
        if e.response.status_code == 401:
            error_info['code'] = 'UNAUTHORIZED'
        elif e.response.status_code == 403:
            error_info['code'] = 'FORBIDDEN'
        else:
            error_info['code'] = 'HTTP_ERROR'
            error_info['status_code'] = e.response.status_code
        return [], 0, error_info
    except requests.exceptions.RequestException as e:
        print(f"Error getting Calibre books: {e}")
        url_from_req = e.request.url if e.request else full_url
        return [], 0, {'code': 'REQUEST_EXCEPTION', 'message': str(e), 'calibre_url': url_from_req}
def format_reading_time(seconds):
    if not seconds or seconds == 0:
        return _("0 minutes")
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return _("%(hours)s hours %(minutes)s minutes", hours=int(hours), minutes=int(minutes))
    return _("%(minutes)s minutes", minutes=int(minutes))

@main_bp.route('/')
@login_required
def index():
    search_query = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    calibre_books, total_calibre_books, calibre_error = get_calibre_books(search_query, page, page_size)
    
    anx_books = get_anx_books(g.user.username)
    for book in anx_books:
        book['formatted_reading_time'] = format_reading_time(book['total_reading_time'])

    total_pages = math.ceil(total_calibre_books / page_size) if page_size > 0 else 0
    pagination = {'page': page, 'page_size': page_size, 'total_books': total_calibre_books, 'total_pages': total_pages}
    
    response = make_response(render_template('index.html',
                           calibre_books=calibre_books,
                           anx_books=anx_books,
                           search_query=search_query,
                           pagination=pagination,
                           calibre_error=calibre_error))
    response.headers['Accept-CH'] = 'Sec-CH-Prefers-Color-Scheme'
    return response
@main_bp.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js')

@main_bp.route('/manifest.webmanifest')
def dynamic_manifest():
    """动态生成 PWA manifest，根据用户主题设置调整背景色"""
    from flask import jsonify
    
    # 基础 manifest 配置
    manifest = {
        "name": "Anx Calibre Manager",
        "short_name": "AnxCalibre",
        "description": "A web-based manager for your Calibre and Anx ebook libraries.",
        "start_url": "/",
        "display": "standalone",
        "theme_color": "#ffffff",  # Default to light
        "icons": [
            {
                "src": "/static/logo.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/logo.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ]
    }
    
    # 根据用户主题设置调整背景色
    if g.user and hasattr(g.user, 'theme'):
        user_theme = g.user.theme or 'auto'
        
        if user_theme == 'dark':
            manifest["background_color"] = "#121212"
            manifest["theme_color"] = "#1f1f1f"
        elif user_theme == 'light':
            manifest["background_color"] = "#ffffff"
            manifest["theme_color"] = "#ffffff"
        else:  # auto
            # Check for Client Hint header to respect browser preference
            if request.headers.get('Sec-CH-Prefers-Color-Scheme') == 'dark':
                manifest["background_color"] = "#121212"
                manifest["theme_color"] = "#1f1f1f"
            else:
                # Default to light if header is not present or not 'dark'
                manifest["background_color"] = "#ffffff"
                manifest["theme_color"] = "#ffffff"
    else:
        # Default for non-logged-in users
        manifest["background_color"] = "#ffffff"
        manifest["theme_color"] = "#ffffff"
    
    response = jsonify(manifest)
    response.headers['Content-Type'] = 'application/manifest+json'
    return response

@main_bp.route('/settings')
@login_required
def settings_page():
    return render_template('settings.html')

@main_bp.route('/reader/<book_type>/<int:book_id>')
@login_required
def reader_page(book_type, book_id):
    return render_template('reader.html', book_type=book_type, book_id=book_id)

@main_bp.route('/audio_player')
@login_required
def audio_player_page():
    theme = g.user.theme if hasattr(g.user, 'theme') and g.user.theme else 'auto'
    library_id = request.args.get('library_id', 'calibre')
    user_info = {
        'id': g.user.id,
        'is_maintainer': g.user.is_maintainer
    }
    return render_template('audio_player.html', theme=theme, library_id=library_id, user_info=user_info)

@main_bp.route('/calibre_cover/<int:book_id>')
@login_required
def calibre_cover(book_id):
    cover_content = get_calibre_cover_data(book_id)
    if cover_content:
        return send_file(io.BytesIO(cover_content), mimetype='image/jpeg')
    return redirect("https://via.placeholder.com/150x220.png?text=Cover+Error")


@main_bp.route('/anx_cover/<path:cover_path>')
@login_required
def anx_cover(cover_path):
    webdav_root = config_manager.config.get("WEBDAV_ROOT")
    if not webdav_root:
        return redirect("https://via.placeholder.com/150x220.png?text=Cover+Error")
    
    safe_username = os.path.basename(g.user.username)
    full_data_dir = os.path.join(webdav_root, safe_username, 'anx', 'data')
    return send_from_directory(full_data_dir, cover_path)

@main_bp.route('/anx_cover_public/<username>/<path:cover_path>')
def anx_cover_public(username, cover_path):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

    # Allow access if the user is logged in and accessing their own cover, or if the stats are public
    is_owner = g.user and hasattr(g.user, 'username') and g.user.username == username
    if not (user and (user['stats_public'] or is_owner)):
        return redirect("https://via.placeholder.com/150x220.png?text=Cover+Error")

    webdav_root = config_manager.config.get("WEBDAV_ROOT")
    if not webdav_root:
        return redirect("https://via.placeholder.com/150x220.png?text=Cover+Error")

    safe_username = os.path.basename(user['username'])
    full_data_dir = os.path.join(webdav_root, safe_username, 'anx', 'data')
    
    if not os.path.exists(os.path.join(full_data_dir, cover_path)):
        return redirect("https://via.placeholder.com/150x220.png?text=Cover+Error")

    return send_from_directory(full_data_dir, cover_path)