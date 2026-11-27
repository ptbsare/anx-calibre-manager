import re
import os
import tempfile
from typing import Dict, Any
import ebooklib
from ebooklib import epub

# 延迟导入以避免循环依赖
def _get_processed_epub_for_book(*args, **kwargs):
    from blueprints.api.books import _get_processed_epub_for_book as func
    return func(*args, **kwargs)

def _get_processed_epub_for_anx_book(*args, **kwargs):
    from blueprints.api.books import _get_processed_epub_for_anx_book as func
    return func(*args, **kwargs)

from .epub_chapter_parser import extract_text_from_html

def _extract_from_ebooklib(book: epub.EpubBook) -> Dict[str, Any]:
    """严格按照 M4B 标签逻辑，从 ebooklib.EpubBook 对象中提取补充元数据。"""
    meta = {}
    if publisher_meta := book.get_metadata('DC', 'publisher'):
        meta['publisher'] = publisher_meta[0][0]
    if date_meta := book.get_metadata('DC', 'date'):
        year_match = re.search(r'\d{4}', date_meta[0][0])
        if year_match:
            meta['pubdate'] = year_match.group(0)
    if description_meta := book.get_metadata('DC', 'description'):
        # 在源头清理从 EPUB 内部提取的 description
        meta['comments'] = extract_text_from_html(description_meta[0][0]) # 使用 comments 键以匹配 Calibre
    if subject_meta := book.get_metadata('DC', 'subject'):
        meta['tags'] = [s[0] for s in subject_meta]
    if language_meta := book.get_metadata('DC', 'language'):
        meta['language'] = language_meta[0][0]
    for identifier in book.get_metadata('DC', 'identifier'):
        try:
            if 'scheme' in identifier[1] and identifier[1]['scheme'].upper() == 'ISBN':
                meta['isbn'] = identifier[0]
                break
        except (IndexError, KeyError):
            continue
    return meta

def _get_epub_cover_image(book: epub.EpubBook) -> bytes | None:
    """从 ebooklib.EpubBook 对象中提取封面图片数据。"""
    try:
        # 策略 1: 尝试获取明确标记为 'cover' 的图片
        if cover_items := list(book.get_items_of_type(ebooklib.ITEM_COVER)):
            return cover_items[0].get_content()
        
        # 策略 2: 回退查找文件名中包含 'cover' 的图片
        for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
            if 'cover' in item.get_name().lower():
                return item.get_content()

        # 策略 3: 最终回退，返回书中的第一张图片
        if images := list(book.get_items_of_type(ebooklib.ITEM_IMAGE)):
            return images[0].get_content()
            
    except Exception:
        # 忽略提取封面时可能发生的任何错误
        pass
    return None

def get_metadata(library_type: str, book_id: int, user_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    获取书籍元数据的最终策略函数。
    - 标题和作者只从数据库获取。
    - 其他所有元数据都从 EPUB 文件本身提取。
    - 本函数自包含 EPUB 获取逻辑。
    """
    final_meta = {}
    db_meta = {}

    # --- 步骤 1: 从数据库获取核心权威元数据 (Title, Authors) 和其他可用字段 ---
    if library_type == 'calibre':
        from blueprints.api.calibre import get_calibre_book_details
        from .epub_chapter_parser import extract_text_from_html
        db_meta = get_calibre_book_details(book_id) or {}
        
        # 清理 comments 字段的 HTML
        if 'comments' in db_meta:
            db_meta['comments'] = extract_text_from_html(db_meta['comments'])

        final_meta['title'] = db_meta.get('title', 'Untitled')
        final_meta['authors'] = db_meta.get('authors', ['Unknown Author'])
    elif library_type == 'anx':
        from anx_library import get_anx_book_details
        from .epub_chapter_parser import extract_text_from_html
        db_meta = get_anx_book_details(user_dict.get('username'), book_id, as_dict=True) or {}

        # 清理 description 字段的 HTML
        if 'description' in db_meta:
            db_meta['description'] = extract_text_from_html(db_meta['description'])

        final_meta['title'] = db_meta.get('title', 'Untitled')
        author = db_meta.get('author')
        final_meta['authors'] = [author] if author else ['Unknown Author']

    # --- 步骤 2: 获取 EPUB 内容并提取补充元数据 ---
    epub_content, _unused1, _unused2 = (None, None, None)
    if library_type == 'calibre':
        language = (user_dict.get('language') or 'zh').split('_')[0]
        epub_content, _unused1, _unused2 = _get_processed_epub_for_book(book_id, user_dict, language=language)
    elif library_type == 'anx':
        epub_content, _unused1, _unused2 = _get_processed_epub_for_anx_book(book_id, user_dict)

    if epub_content:
        with tempfile.NamedTemporaryFile(suffix='.epub', delete=True) as temp_file:
            temp_file.write(epub_content)
            temp_file.flush()
            try:
                book = epub.read_epub(temp_file.name)
                epub_meta = _extract_from_ebooklib(book)
                # 合并，数据库中的核心字段不会被覆盖
                final_meta.update(epub_meta)
                # 额外提取封面
                final_meta['cover_image_data'] = _get_epub_cover_image(book)
            except Exception as e:
                print(f"Warning: Could not parse EPUB metadata: {e}")
    
    # --- 步骤 3: 确保数据库中的字段优先（特别是 comments/description） ---
    # Calibre 使用 'comments', Anx 使用 'description'
    if db_meta.get('comments'):
        final_meta['comments'] = db_meta['comments']
    elif db_meta.get('description'):
        final_meta['comments'] = db_meta['description'] # 统一写入 'comments'

    # 其他在 db_meta 中存在但在 final_meta 中可能被 epub_meta 覆盖的字段
    for key in ['publisher', 'pubdate', 'tags', 'language']:
        if db_meta.get(key):
            final_meta[key] = db_meta[key]

    return final_meta