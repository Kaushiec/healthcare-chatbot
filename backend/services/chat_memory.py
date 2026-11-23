"""Local prototype MySQL short-term chat history. Not a multi-user auth system."""
import json
from uuid import uuid4, UUID
from backend.database import get_connection


def _valid_id(session_id):
    if not isinstance(session_id, str):
        return None
    try:
        x = UUID(session_id)
    except (TypeError, ValueError, AttributeError):
        return None
    return str(x) if x.version == 4 else None


def get_or_create_session(session_id=None):
    provided = _valid_id(session_id)
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        if provided:
            cursor.execute("SELECT id FROM chat_sessions WHERE id=%s", (provided,))
            if cursor.fetchone():
                return provided
        sid = str(uuid4())
        cursor.execute("INSERT INTO chat_sessions (id) VALUES (%s)", (sid,))
        connection.commit()
        return sid
    finally:
        cursor.close()
        connection.close()


def _decode_json(raw):
    if raw is None:
        return None
    if isinstance(raw, (dict, list)):
        return raw
    return json.loads(raw)


def read_context(session_id, history_limit=8):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT last_intent, pending_intent FROM chat_sessions WHERE id=%s",
            (session_id,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError("Unknown session")
        cursor.execute(
            "SELECT role, content FROM chat_messages WHERE session_id=%s "
            "ORDER BY id DESC LIMIT %s", (session_id, int(history_limit)))
        recent = list(reversed(cursor.fetchall()))
        return {"history": recent, "last_intent": _decode_json(row["last_intent"]),
                "pending_intent": _decode_json(row["pending_intent"])}
    finally:
        cursor.close()
        connection.close()


def save_exchange(session_id, question, answer, last_intent=None, pending_intent=None):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO chat_messages (session_id, role, content) "
            "VALUES (%s, 'user', %s)", (session_id, question[:2000]))
        cursor.execute(
            "INSERT INTO chat_messages (session_id, role, content) "
            "VALUES (%s, 'assistant', %s)", (session_id, answer[:3000]))
        cursor.execute("UPDATE chat_sessions SET last_intent=%s, pending_intent=%s "
                       "WHERE id=%s",
                       (json.dumps(last_intent) if last_intent is not None else None,
                        json.dumps(pending_intent) if pending_intent is not None else None,
                        session_id))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()
