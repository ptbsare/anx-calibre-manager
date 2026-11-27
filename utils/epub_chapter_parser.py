# -*- coding: utf-8 -*-
import logging
import zipfile
import re
import os
import json
import tempfile
from typing import List, Tuple, Dict, Any

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

# This is a key dependency from another utils file
from .epub_utils import _process_entire_epub

# 延迟导入以避免循环依赖
def _get_processed_epub_for_book(*args, **kwargs):
    from blueprints.api.books import _get_processed_epub_for_book as func
    return func(*args, **kwargs)

def _get_processed_epub_for_anx_book(*args, **kwargs):
    from blueprints.api.books import _get_processed_epub_for_anx_book as func
    return func(*args, **kwargs)

logger = logging.getLogger(__name__)

# --- 缓存设置 ---
CACHE_DIR = "/tmp/anx_chapter_cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def extract_text_from_html(html_content: str) -> str:
    """
    从HTML内容中稳健地提取和清理文本，并将段落间隔统一为 '\n\n'。
    """
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'lxml')
    
    # 移除所有不需要的标签
    for element in soup(["script", "style", "head", "title", "meta", "[document]"]):
        element.decompose()

    # 将 <br> 标签替换为单个换行符，以保留段内换行
    for br in soup.find_all("br"):
        br.replace_with("\n")

    # 在所有块级元素的末尾添加双换行符，以创建段落间隔
    for block_tag in soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'tr', 'blockquote', 'section']):
        block_tag.append('\n\n')

    # 使用 separator='' 来获取文本，这样我们添加的换行符就会被保留
    raw_text = soup.get_text(separator='')
    
    # --- 后续清理 ---
    # 1. 将多个连续的空格或制表符压缩为单个空格
    cleaned_text = re.sub(r'[ \t]+', ' ', raw_text)
    # 2. 移除每行开头和结尾的空格
    cleaned_text = re.sub(r'^[ \t]+|[ \t]+$', '', cleaned_text, flags=re.MULTILINE)
    # 3. 移除紧跟在换行符前后的空格
    cleaned_text = re.sub(r' *\n *', '\n', cleaned_text)
    # 4. 将三个或更多的连续换行符合并为两个（一个空行，即段落分隔）
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    
    final_text = cleaned_text.strip()
    
    return final_text


# ==============================================================================
#  START: 原封不动保留的三级回退策略原始逻辑
# ==============================================================================

def _get_epub_chapters_level1_mcp(epub_path: str) -> List[Tuple[str, str]]:
    """
    第一级提取策略：使用高性能函数，返回 (标题, 纯文本)。
    """
    try:
        processed_data = _process_entire_epub(epub_path)
        if 'error' in processed_data:
            logger.error(f"Level 1 MCP processor failed: {processed_data['error']}")
            return []
        
        chapters = []
        for chapter_data in processed_data.get('processed_chapters', []):
            title = chapter_data.get('title', 'Untitled Chapter')
            html_content = chapter_data.get('html_content', '')
            plain_text = extract_text_from_html(html_content)
            if plain_text:
                chapters.append((title, plain_text))
        return chapters
    except Exception as e:
        logger.error(f"Exception in Level 1 MCP processor: {e}")
        return []


def _get_epub_chapters_level2_legacy(book: epub.EpubBook) -> List[Tuple[str, str]]:
    """
    第二级提取策略：使用旧版文档流解析，返回 (标题, 纯文本)。
    """
    chapters = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        content = item.get_content()
        soup = BeautifulSoup(content, "lxml-xml")
        
        title = ""
        for level in ['h1', 'h2', 'h3', 'title']:
            if tag := soup.find(level):
                title = tag.get_text().strip()
                break
        if not title:
            title = item.get_name() or item.file_name

        plain_text = extract_text_from_html(str(soup))
        
        if plain_text:
            chapters.append((title, plain_text))
    return chapters


def _get_epub_chapters_level3_spine(book: epub.EpubBook, epub_path: str) -> List[Tuple[str, str]]:
    """
    第三级提取策略：基于 Spine 的手动解析，返回 (标题, 纯文本)。
    此策略通过直接扫描 zip 存档来稳健地定位 OPF 目录。
    """
    chapters = []
    if not book.spine:
        logger.warning("EPUB has no spine. Cannot use Level 3 extraction.")
        return chapters
        
    try:
        with zipfile.ZipFile(epub_path, 'r') as archive:
            # --- 新增：稳健地查找 OPF 目录 ---
            # 不再信任 book.opf_dir，而是通过扫描 zip 文件列表来查找 .opf 文件。
            opf_dir = ''
            # 标准方式：先检查 META-INF/container.xml
            try:
                container_content = archive.read('META-INF/container.xml').decode('utf-8', 'ignore')
                rootfile_path_match = re.search(r'full-path="([^"]+)"', container_content)
                if rootfile_path_match:
                    opf_full_path = rootfile_path_match.group(1)
                    opf_dir = os.path.dirname(opf_full_path)
                    logger.info(f"Level 3: Found OPF path '{opf_full_path}' from container.xml. OPF dir is '{opf_dir}'.")
            except (KeyError, AttributeError):
                 # 回退方式：如果 container.xml 失败，则扫描整个存档
                logger.warning("Level 3: Could not find or parse container.xml, scanning for .opf file.")
                for filename in archive.namelist():
                    if filename.lower().endswith('.opf'):
                        opf_dir = os.path.dirname(filename)
                        logger.info(f"Level 3: Found OPF file by scanning: '{filename}'. OPF dir is '{opf_dir}'.")
                        break
            
            # --- TOC 标题映射 ---
            toc_title_map = {}
            if book.toc:
                toc_items = book.toc if isinstance(book.toc, (list, tuple)) else [book.toc]
                for item in toc_items:
                    def process_toc_item(toc_item):
                        if isinstance(toc_item, ebooklib.epub.Link):
                            toc_title_map[toc_item.href.split('#')[0]] = toc_item.title
                        elif isinstance(toc_item, (list, tuple)):
                            for sub_item in toc_item:
                                process_toc_item(sub_item)
                    process_toc_item(item)

            # --- 遍历 Spine ---
            for item_id, _ in book.spine:
                item = book.get_item_with_id(item_id)
                if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
                    relative_file_name = item.file_name
                    title = toc_title_map.get(relative_file_name, item.get_name() or relative_file_name)
                    
                    # 使用找到的 opf_dir 构建完整路径
                    full_path_in_zip = os.path.join(opf_dir, relative_file_name).replace('\\', '/')

                    try:
                        content = archive.read(full_path_in_zip).decode('utf-8', 'ignore')
                        plain_text = extract_text_from_html(content)
                        if plain_text:
                            chapters.append((title, plain_text))
                    except KeyError:
                        logger.warning(f"File '{full_path_in_zip}' not found in EPUB archive. Skipping.")
                    except Exception as e:
                        logger.error(f"Error reading file '{full_path_in_zip}' from EPUB: {e}")
    except Exception as e:
        logger.error(f"Failed to process EPUB with Level 3 (spine) method: {e}")

    return chapters


def _run_chapter_extraction_strategy(book: epub.EpubBook, epub_path: str) -> List[Tuple[str, str]]:
    """
    这是三级回退策略的原始调度器。
    """
    # --- Level 1: MCP 高性能解析器 ---
    logger.info("Attempting chapter extraction strategy: Level 1 (MCP Processor)...")
    chapters_l1 = _get_epub_chapters_level1_mcp(epub_path)
    len_l1 = sum(len(content) for _, content in chapters_l1)
    logger.info(f"Level 1 Result: {len(chapters_l1)} chapters, Total Text Length: {len_l1}")
    if len_l1 > 500:
        logger.info("Level 1 provided a good result, using it directly.")
        return chapters_l1

    # --- Level 2 & 3 & 比较 ---
    logger.info("Attempting chapter extraction strategy: Level 2 (Legacy Document Stream)...")
    chapters_l2 = _get_epub_chapters_level2_legacy(book)
    len_l2 = sum(len(content) for _, content in chapters_l2)
    logger.info(f"Level 2 Result: {len(chapters_l2)} chapters, Total Text Length: {len_l2}")

    logger.info("Attempting chapter extraction strategy: Level 3 (Spine Fallback)...")
    chapters_l3 = _get_epub_chapters_level3_spine(book, epub_path)
    len_l3 = sum(len(content) for _, content in chapters_l3)
    logger.info(f"Level 3 Result: {len(chapters_l3)} chapters, Total Text Length: {len_l3}")

    results = [
        (len_l1, chapters_l1, "Level 1"),
        (len_l2, chapters_l2, "Level 2"),
        (len_l3, chapters_l3, "Level 3")
    ]
    best_len, best_chapters, best_level_name = max(results, key=lambda item: item[0])
    logger.info(f"Selected best result from {best_level_name}.")
    return best_chapters

# ==============================================================================
#  END: 三级回退策略原始逻辑
# ==============================================================================


def get_parsed_chapters(library_type: str, book_id: int, user_dict: Dict[str, Any]) -> List[Tuple[str, str]]:
    """
    统一的、带缓存的函数，用于获取任何书籍的已解析章节列表 (标题, 纯文本)。
    这是所有上层应用应该调用的唯一入口。
    """
    cache_key = f"{library_type}-{book_id}-user{user_dict['id']}.json"
    cache_path = os.path.join(CACHE_DIR, cache_key)

    # 1. 检查缓存
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                logger.info(f"Cache hit for {library_type}-{book_id}. Loading from cache.")
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            logger.warning(f"Failed to read cache file {cache_path}. Re-parsing.")

    # 2. 获取标准化的 EPUB 内容
    logger.info(f"Cache miss for {library_type}-{book_id}. Processing book.")
    epub_content, epub_filename, _ = (None, None, None)
    if library_type == 'calibre':
        language = (user_dict.get('language') or 'zh').split('_')[0]
        epub_content, epub_filename, _ = _get_processed_epub_for_book(book_id, user_dict, language=language)
    elif library_type == 'anx':
        epub_content, epub_filename, _ = _get_processed_epub_for_anx_book(book_id, user_dict)
    
    if not epub_content or epub_filename is None:
        raise ValueError(f"Failed to get processed EPUB for {library_type}-{book_id}. Reason: {epub_filename or 'Unknown'}")

    # 3. 将 EPUB 内容写入临时文件并执行原始的解析策略
    chapters = []
    with tempfile.NamedTemporaryFile(suffix='.epub', delete=True) as temp_file:
        temp_file.write(epub_content)
        temp_file.flush()
        
        book = epub.read_epub(temp_file.name)
        chapters = _run_chapter_extraction_strategy(book, temp_file.name)

    if not chapters:
        raise ValueError(f"Failed to parse chapters from EPUB for {library_type}-{book_id}")

    # 4. 写入缓存
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(chapters, f, ensure_ascii=False)
        logger.info(f"Successfully cached parsed content for {library_type}-{book_id}.")
    except IOError as e:
        logger.error(f"Failed to write to cache file {cache_path}: {e}")

    return chapters