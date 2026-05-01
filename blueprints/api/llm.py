import requests
import uuid
import json
import os
import time
from flask import Blueprint, request, jsonify, g, Response, current_app
from flask_babel import gettext as _
from contextlib import closing
import database
from threading import Lock
from utils.activity_logger import log_activity, ActivityType
from utils.decorators import login_required_api

# Use a try-except block for cleaner optional import
try:
    from blueprints.mcp import get_entire_book_content
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

llm_bp = Blueprint('llm', __name__, url_prefix='/api/llm')

def _generate_llm_response(session_id, book_id, book_type, user_info_dict, translated_strings, app, user_message_id=None):
    """
    Internal generator function to handle LLM response generation.
    It receives all necessary data as arguments to avoid working outside of an application context.
    """
    # --- Pre-fetch translated strings to use in the generator safely ---
    extracting_msg = translated_strings['extracting_book_content']
    thinking_msg = translated_strings['waiting_for_model']
    get_content_fail_msg = translated_strings['failed_to_get_book_content']
    extract_text_fail_msg = translated_strings['could_not_extract_text']
    llm_config_fail_msg = translated_strings['llm_settings_not_configured']
    llm_comm_fail_msg = translated_strings['llm_communication_failed']

    # --- Get book content ---
    stage_message = json.dumps({"stage": "extracting", "message": extracting_msg})
    yield f"event: stage_update\ndata: {stage_message}\n\n"

    content_result = {}
    with app.app_context():
        g.user = user_info_dict
        content_result = get_entire_book_content(library_type=book_type, book_id=book_id)

    if 'error' in content_result:
        error_text = get_content_fail_msg % {'error': content_result['error']}
        yield f"event: error\ndata: {json.dumps({'error': error_text})}\n\n"
        return
    
    book_content = content_result.get('full_text', '')
    if not book_content:
        yield f"event: error\ndata: {json.dumps({'error': extract_text_fail_msg})}\n\n"
        return

    # --- Prepare for LLM call ---
    stage_message = json.dumps({"stage": "thinking", "message": thinking_msg})
    yield f"event: stage_update\ndata: {stage_message}\n\n"
    
    if not all([user_info_dict['llm_base_url'], user_info_dict['llm_api_key'], user_info_dict['llm_model']]):
        yield f"event: error\ndata: {json.dumps({'error': llm_config_fail_msg})}\n\n"
        return

    headers = {'Authorization': f"Bearer {user_info_dict['llm_api_key']}", 'Content-Type': 'application/json'}
    endpoint = user_info_dict['llm_base_url'].rstrip('/') + '/chat/completions'
    
    messages = [{"role": "system", "content": translated_strings['base_system_prompt']}]
    
    with closing(database.get_db()) as db:
        history = db.execute(
            'SELECT role, content FROM llm_chat_messages WHERE session_id = ? ORDER BY created_at ASC',
            (session_id,)
        ).fetchall()

    book_context_prompt = translated_strings['book_context_prompt_template'] % {'book_content': book_content}
    
    if not history:
        summary_request_prompt = translated_strings['summary_request_prompt']
        virtual_user_message_content = f"{book_context_prompt} {summary_request_prompt}"
        messages.append({"role": "user", "content": virtual_user_message_content})
    else:
        messages.append({"role": "user", "content": book_context_prompt})

    for msg in history:
        messages.append({"role": msg['role'], "content": msg['content']})

    payload = {
        "model": user_info_dict['llm_model'],
        "messages": messages,
        "stream": True
    }

    session_data = {"session_id": session_id}
    if user_message_id:
        session_data["user_message_id"] = user_message_id
    yield f"event: session_start\ndata: {json.dumps(session_data)}\n\n"

    stage_message = json.dumps({"stage": "thinking", "message": thinking_msg})
    yield f"event: stage_update\ndata: {stage_message}\n\n"

    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=300, stream=True)
        response.raise_for_status()

        full_response_content = []
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data: '):
                    json_str = decoded_line[6:]
                    if json_str.strip() == '[DONE]':
                        break
                    
                    data = json.loads(json_str)
                    if 'choices' in data and data['choices'] and data['choices'][0].get('delta', {}).get('content'):
                        chunk = data['choices'][0]['delta']['content']
                        full_response_content.append(chunk)
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
        final_text = "".join(full_response_content)
        with closing(database.get_db()) as db:
            cursor = db.cursor()
            cursor.execute(
                'INSERT INTO llm_chat_messages (session_id, role, content) VALUES (?, ?, ?)',
                (session_id, 'assistant', final_text)
            )
            model_message_id = cursor.lastrowid
            
            # Update the session's updated_at timestamp
            cursor.execute(
                'UPDATE llm_chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (session_id,)
            )
            
            # Get the updated timestamp
            session_info = cursor.execute(
                'SELECT updated_at FROM llm_chat_sessions WHERE id = ?',
                (session_id,)
            ).fetchone()
            db.commit()

        yield f"event: end\ndata: {json.dumps({'model_message_id': model_message_id, 'updated_at': session_info['updated_at'] if session_info else None})}\n\n"

    except Exception as e:
        error_text = llm_comm_fail_msg % {'error': str(e)}
        yield f"event: error\ndata: {json.dumps({'error': error_text})}\n\n"

@llm_bp.route('/history', methods=['GET'])
@login_required_api
def get_chat_history():
    book_id = request.args.get('book_id', type=int)
    book_type = request.args.get('book_type')

    if not book_id or not book_type:
        return jsonify({'error': _('Book ID and type are required.')}), 400

    with closing(database.get_db()) as db:
        session = db.execute(
            'SELECT id FROM llm_chat_sessions WHERE user_id = ? AND book_id = ? AND book_type = ? ORDER BY created_at DESC LIMIT 1',
            (g.user.id, book_id, book_type)
        ).fetchone()

        if not session:
            return jsonify({'error': _('No history found for this book.')}), 404

        messages = db.execute(
            'SELECT id, role, content FROM llm_chat_messages WHERE session_id = ? ORDER BY created_at ASC',
            (session['id'],)
        ).fetchall()

    return jsonify({
        'session_id': session['id'],
        'messages': [dict(msg) for msg in messages]
    })

@llm_bp.route('/chat', methods=['POST'])
@login_required_api
def chat_with_book():
    if not MCP_AVAILABLE:
        return jsonify({'error': _('MCP module is not available, cannot process book content.')}), 501

    data = request.get_json()
    session_id = data.get('session_id')
    book_id = data.get('book_id')
    book_type = data.get('book_type')
    book_title = data.get('book_title')
    user_message = data.get('message')

    if not all([book_id, book_type, book_title, user_message]):
        return jsonify({'error': _('Missing required fields.')}), 400

    # 标记是否为新会话
    is_new_session = not session_id
    
    with closing(database.get_db()) as db:
        cursor = db.cursor()
        if is_new_session:
            session_id = str(uuid.uuid4())
            cursor.execute(
                'INSERT INTO llm_chat_sessions (id, user_id, book_id, book_type, book_title) VALUES (?, ?, ?, ?, ?)',
                (session_id, g.user.id, book_id, book_type, book_title)
            )
            # 记录新会话开始
            log_activity(ActivityType.LLM_CHAT_START, book_id=book_id, book_title=book_title, library_type=book_type, success=True)
        else:
            # Update the session's updated_at when user sends a message
            cursor.execute(
                'UPDATE llm_chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (session_id,)
            )
        
        cursor.execute(
            'INSERT INTO llm_chat_messages (session_id, role, content) VALUES (?, ?, ?)',
            (session_id, 'user', user_message)
        )
        user_message_id = cursor.lastrowid
        db.commit()
        
        # 记录LLM对话消息
        log_activity(ActivityType.LLM_CHAT_MESSAGE, book_id=book_id, book_title=book_title, library_type=book_type, success=True)

    app = current_app._get_current_object()
    user_info_dict = {key: getattr(g.user, key, None) for key in
                      ['id', 'username', 'language', 'kindle_email', 'anx_token', 'anx_url']}

    # Load LLM settings with fallback to global defaults
    from config_manager import config
    user_info_dict['llm_base_url'] = g.user.llm_base_url or config.get('DEFAULT_LLM_BASE_URL')
    user_info_dict['llm_api_key'] = g.user.llm_api_key or config.get('DEFAULT_LLM_API_KEY')
    user_info_dict['llm_model'] = g.user.llm_model or config.get('DEFAULT_LLM_MODEL')
    
    current_time_str = time.strftime('%Y-%m-%d %H:%M:%S %Z')
    time_prompt = _("Current time is %(current_time)s.", current_time=current_time_str)
    base_prompt = _("You are a helpful assistant. The user is asking about the book '%(book_title)s'.") % {'book_title': book_title}
    mermaid_prompt = _("You can use mermaid syntax for diagrams by enclosing it in ```mermaid ... ```.")
    MERMAID_SPECIAL_CHARS = "():;\\`"
    mermaid_prompt_instruction = _(
        "IMPORTANT Mermaid Rules:\n"
        "1. Node IDs must be single words (no spaces or special characters).\n"
        "2. Titles and all kinds of descriptive texts containing special characters like `():;\"` MUST be in quotes: `\"text\"`.\n"
        "3. **Crucially, do NOT use colons to add labels to nodes, like `A --> B: text`. This is invalid.** Instead, define the node label separately: `A --> B; B[\"text\"]`.\n"
        "4. Use valid arrow types: `-->`, `---`, `==>`. \n"
        "5. Do not use `style` or `linkStyle` definitions; the theme is handled automatically."
    )

    translated_strings = {
        'base_system_prompt': f"{time_prompt} {base_prompt} {mermaid_prompt} {mermaid_prompt_instruction}",
        'invalid_book_type': _('Invalid book type.'),
        'failed_to_get_book_content': _('Failed to get book content: %(error)s'),
        'could_not_extract_text': _('Could not extract text from the book.'),
        'llm_settings_not_configured': _('LLM settings are not configured in user settings.'),
        'book_context_prompt_template': _(" Here is the full text of the book:\n\n---BOOK CONTENT---\n%(book_content)s\n---END BOOK CONTENT---"),
        'summary_request_prompt': _("Please provide a comprehensive summary and a profound review of this book."),
        'llm_communication_failed': _('Failed to communicate with LLM provider: %(error)s'),
        'extracting_book_content': _('Extracting entire book content...'),
        'waiting_for_model': _('Thinking...'),
    }

    generator = _generate_llm_response(session_id, book_id, book_type, user_info_dict, translated_strings, app, user_message_id=user_message_id)
    return Response(generator, mimetype='text/event-stream')

@llm_bp.route('/regenerate', methods=['POST'])
@login_required_api
def regenerate_chat_response():
    data = request.get_json()
    message_id = data.get('message_id')

    if not message_id:
        return jsonify({'error': _('Message ID is required.')}), 400

    with closing(database.get_db()) as db:
        msg_info = db.execute(
            'SELECT s.id as session_id, s.user_id, s.book_id, s.book_type, s.book_title, m.created_at '
            'FROM llm_chat_messages m '
            'JOIN llm_chat_sessions s ON m.session_id = s.id '
            'WHERE m.id = ?', (message_id,)
        ).fetchone()

        if not msg_info:
            return jsonify({'error': _('Message not found.')}), 404
        if msg_info['user_id'] != g.user.id:
            return jsonify({'error': _('Permission denied.')}), 403

        db.execute(
            'DELETE FROM llm_chat_messages WHERE session_id = ? AND created_at > ?',
            (msg_info['session_id'], msg_info['created_at'])
        )
        # Also update the session's updated_at timestamp
        db.execute(
            'UPDATE llm_chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (msg_info['session_id'],)
        )
        db.commit()
        
        # 记录重新生成活动
        log_activity(ActivityType.LLM_CHAT_MESSAGE, book_id=msg_info['book_id'], book_title=msg_info['book_title'], library_type=msg_info['book_type'], success=True, detail=_('Regenerate response'))
    
    app = current_app._get_current_object()
    user_obj = database.get_db().execute('SELECT * FROM users WHERE id = ?', (msg_info['user_id'],)).fetchone()
    user_info_dict = {key: user_obj[key] for key in user_obj.keys() if key not in ['llm_base_url', 'llm_api_key', 'llm_model']}

    # Load LLM settings with fallback to global defaults
    from config_manager import config
    user_info_dict['llm_base_url'] = user_obj['llm_base_url'] or config.get('DEFAULT_LLM_BASE_URL')
    user_info_dict['llm_api_key'] = user_obj['llm_api_key'] or config.get('DEFAULT_LLM_API_KEY')
    user_info_dict['llm_model'] = user_obj['llm_model'] or config.get('DEFAULT_LLM_MODEL')
    
    current_time_str = time.strftime('%Y-%m-%d %H:%M:%S %Z')
    time_prompt = _("Current time is %(current_time)s.", current_time=current_time_str)
    base_prompt = _("You are a helpful assistant. The user is asking about the book '%(book_title)s'.") % {'book_title': msg_info['book_title']}
    mermaid_prompt = _("You can use mermaid syntax for diagrams by enclosing it in ```mermaid ... ```.")
    mermaid_prompt_instruction = _(
        "IMPORTANT Mermaid Rules:\n"
        "1. Node IDs must be single words (no spaces or special characters).\n"
        "2. Descriptive text containing special characters like `():;\"` MUST be in quotes: `\"text\"`.\n"
        "3. **Crucially, do NOT use colons to add labels to nodes, like `A --> B: text`. This is invalid.** Instead, define the node label separately: `A --> B; B[\"text\"]`.\n"
        "4. Use valid arrow types: `-->`, `---`, `==>`. \n"
        "5. Do not use `style` or `linkStyle` definitions; the theme is handled automatically."
    )

    translated_strings = {
        'base_system_prompt': f"{time_prompt} {base_prompt} {mermaid_prompt} {mermaid_prompt_instruction}",
        'invalid_book_type': _('Invalid book type.'),
        'failed_to_get_book_content': _('Failed to get book content: %(error)s'),
        'could_not_extract_text': _('Could not extract text from the book.'),
        'llm_settings_not_configured': _('LLM settings are not configured in user settings.'),
        'book_context_prompt_template': _(" Here is the full text of the book:\n\n---BOOK CONTENT---\n%(book_content)s\n---END BOOK CONTENT---"),
        'summary_request_prompt': _("Please provide a comprehensive summary and a profound review of this book."),
        'llm_communication_failed': _('Failed to communicate with LLM provider: %(error)s'),
        'extracting_book_content': _('Extracting entire book content...'),
        'waiting_for_model': _('Thinking...'),
    }

    generator = _generate_llm_response(
        session_id=msg_info['session_id'],
        book_id=msg_info['book_id'],
        book_type=msg_info['book_type'],
        user_info_dict=user_info_dict,
        translated_strings=translated_strings,
        app=app
    )
    return Response(generator, mimetype='text/event-stream')

@llm_bp.route('/models', methods=['POST'])
@login_required_api
def get_llm_models():
    data = request.get_json()
    base_url = data.get('base_url')
    api_key = data.get('api_key')

    if not base_url or not api_key:
        return jsonify({'error': _('Base URL and API Key are required.')}), 400

    headers = {'Authorization': f'Bearer {api_key}'}
    if not base_url.endswith('/'):
        base_url += '/'
    models_url = f"{base_url}models"

    try:
        response = requests.get(models_url, headers=headers, timeout=10)
        response.raise_for_status()
        models_data = response.json()
        
        if 'data' in models_data and isinstance(models_data['data'], list):
            model_ids = sorted([model['id'] for model in models_data['data'] if 'id' in model])
            return jsonify(model_ids)
        else:
            return jsonify({'error': _('Unexpected response format from model provider.')}), 500

    except requests.exceptions.RequestException as e:
        error_message = str(e)
        if '401' in error_message:
            return jsonify({'error': _('Authentication error. Please check your API Key.')}), 401
        elif '404' in error_message:
             return jsonify({'error': _('Invalid API endpoint. Please check your Base URL.')}), 404
        else:
            return jsonify({'error': _('Could not connect to the model provider: %(error)s', error=error_message)}), 500
    except Exception as e:
        return jsonify({'error': _('An unexpected error occurred: %(error)s', error=str(e))}), 500

@llm_bp.route('/session/<session_id>', methods=['DELETE'])
@login_required_api
def delete_chat_session(session_id):
    with closing(database.get_db()) as db:
        session = db.execute(
            'SELECT id FROM llm_chat_sessions WHERE id = ? AND user_id = ?',
            (session_id, g.user.id)
        ).fetchone()

        if not session:
            return jsonify({'error': _('Session not found or permission denied.')}), 404

        # Manually delete messages first to ensure data integrity
        db.execute('DELETE FROM llm_chat_messages WHERE session_id = ?', (session_id,))
        db.execute('DELETE FROM llm_chat_sessions WHERE id = ?', (session_id,))
        db.commit()
    
    log_activity(ActivityType.LLM_DELETE_SESSION, success=True, detail=_('Session ID: %(session_id)s', session_id=session_id))
    return jsonify({'success': True, 'message': _('Chat session deleted successfully.')})


@llm_bp.route('/message/<int:message_id>', methods=['DELETE'])
@login_required_api
def delete_message(message_id):
    db = database.get_db()
    message = db.execute(
        'SELECT s.user_id FROM llm_chat_messages m '
        'JOIN llm_chat_sessions s ON m.session_id = s.id '
        'WHERE m.id = ?',
        (message_id,)
    ).fetchone()

    if message is None:
        return jsonify({'status': 'error', 'message': 'Message not found'}), 404

    if message['user_id'] != g.user.id:
        return jsonify({'status': 'error', 'message': 'Forbidden'}), 403

    db.execute('DELETE FROM llm_chat_messages WHERE id = ?', (message_id,))
    db.commit()
    
    log_activity(ActivityType.LLM_DELETE_MESSAGE, success=True, detail=_('Message ID: %(message_id)s', message_id=message_id))
    return jsonify({'status': 'success', 'message': 'Message deleted successfully'})