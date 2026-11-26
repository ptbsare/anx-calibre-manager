"""Only cover URLs may read an image that stays inside the cover directory."""

import os
import posixpath

COVER_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.avif'}


def is_anx_cover_relpath(cover_path: str) -> bool:
    """True when cover_path is one image file inside the cover directory."""
    if not isinstance(cover_path, str) or not cover_path or '\x00' in cover_path:
        return False
    if cover_path.startswith(('/', '\\')):
        return False
    normalized = posixpath.normpath(cover_path.replace('\\', '/'))
    if normalized in ('.', '..') or normalized.startswith('../') or normalized.startswith('/'):
        return False
    parts = normalized.split('/')
    if len(parts) < 2 or parts[0] != 'cover':
        return False
    if any(part in ('', '.', '..') for part in parts):
        return False
    filename = parts[-1]
    extension = posixpath.splitext(filename)[1].lower()
    return extension in COVER_EXTENSIONS


def is_anx_cover_file(data_dir: str, cover_path: str) -> bool:
    """True when the file is a cover image and does not resolve outside cover/."""
    if not is_anx_cover_relpath(cover_path):
        return False
    cover_root = os.path.realpath(os.path.join(data_dir, 'cover'))
    parts = cover_path.replace('\\', '/').split('/')
    candidate = os.path.realpath(os.path.join(data_dir, *parts))
    if not os.path.isfile(candidate):
        return False
    try:
        return os.path.commonpath([cover_root, candidate]) == cover_root
    except ValueError:
        return False
