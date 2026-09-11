from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone
import json
from typing import Optional, List
from ..database import query_all, query_one, execute_insert, execute_update
from ..auth import get_current_user
from ..schemas import ChatMessageRequest, ConversationCreateRequest, ConversationRenameRequest
from ..ai_service import HospitalAIService

router = APIRouter(prefix="/chatbot", tags=["AI Hospital Assistant"])

@router.get("/conversations")
def get_conversations(query: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    sql = """
        SELECT c.*,
               (SELECT COUNT(*) FROM chat_messages m WHERE m.conversation_id = c.id) as message_count,
               (SELECT m.message_text FROM chat_messages m WHERE m.conversation_id = c.id ORDER BY m.timestamp DESC LIMIT 1) as last_message
        FROM chat_conversations c
        WHERE c.user_id = ?
    """
    params = [user_id]

    if query:
        sql += " AND (LOWER(c.title) LIKE ? OR EXISTS (SELECT 1 FROM chat_messages m WHERE m.conversation_id = c.id AND LOWER(m.message_text) LIKE ?))"
        term = f"%{query.lower()}%"
        params.extend([term, term])

    sql += " ORDER BY c.updated_at DESC"
    return query_all(sql, tuple(params))

@router.post("/conversations", status_code=status.HTTP_201_CREATED)
def create_conversation(req: ConversationCreateRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    now_iso = datetime.now(timezone.utc).isoformat()

    title = req.title or "Hospital Assistance"
    conv_id = execute_insert(
        "INSERT INTO chat_conversations (user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (user_id, title, now_iso, now_iso)
    )

    # Initial system welcome message
    welcome_msg = (
        "👋 Welcome to the **CareSync Clinical OS Digital Assistant**.\n\n"
        "I can help you navigate Indian hospital services, find available specialists, view multi-specialty hospitals across Indian metros, "
        "check consultation fees in ₹, and manage appointments.\n\n"
        "*Notice: I do not provide medical diagnoses. For life-threatening emergencies, dial 108 or visit our 24x7 Emergency Trauma Unit immediately.*"
    )
    execute_insert(
        """INSERT INTO chat_messages (conversation_id, sender_role, message_text, timestamp, metadata_json)
           VALUES (?, 'assistant', ?, ?, NULL)""",
        (conv_id, welcome_msg, now_iso)
    )

    # If user provided initial message
    if req.initial_message:
        execute_insert(
            """INSERT INTO chat_messages (conversation_id, sender_role, message_text, timestamp, metadata_json)
               VALUES (?, 'user', ?, ?, NULL)""",
            (conv_id, req.initial_message, now_iso)
        )
        ai_res = HospitalAIService.answer_hospital_query(req.initial_message, current_user)
        reply_text = ai_res["reply_text"] if isinstance(ai_res, dict) else str(ai_res)
        card_type = ai_res.get("card_type") if isinstance(ai_res, dict) else None
        cards = ai_res.get("cards", []) if isinstance(ai_res, dict) else []
        meta_json = json.dumps({"card_type": card_type, "cards": cards}) if (cards or card_type) else None
        execute_insert(
            """INSERT INTO chat_messages (conversation_id, sender_role, message_text, timestamp, metadata_json)
               VALUES (?, 'assistant', ?, ?, ?)""",
            (conv_id, reply_text, now_iso, meta_json)
        )

    return {"status": "success", "conversation_id": conv_id, "title": title}

@router.get("/conversations/{conversation_id}")
def get_conversation_details(conversation_id: int, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    conv = query_one("SELECT * FROM chat_conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id))
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation thread not found.")

    raw_messages = query_all(
        "SELECT * FROM chat_messages WHERE conversation_id = ? ORDER BY timestamp ASC",
        (conversation_id,)
    )

    messages = []
    for msg in raw_messages:
        m = dict(msg)
        m["cards"] = []
        m["card_type"] = None
        if m.get("metadata_json"):
            try:
                meta = json.loads(m["metadata_json"])
                m["cards"] = meta.get("cards", [])
                m["card_type"] = meta.get("card_type")
            except Exception:
                pass
        messages.append(m)

    return {
        "conversation": conv,
        "messages": messages
    }

@router.post("/conversations/{conversation_id}/messages")
def send_chat_message(conversation_id: int, req: ChatMessageRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    conv = query_one("SELECT * FROM chat_conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id))
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    now_iso = datetime.now(timezone.utc).isoformat()

    # Save user message
    execute_insert(
        """INSERT INTO chat_messages (conversation_id, sender_role, message_text, timestamp, metadata_json)
           VALUES (?, 'user', ?, ?, NULL)""",
        (conversation_id, req.message, now_iso)
    )

    # Generate assistant reply via AI hospital logic
    ai_res = HospitalAIService.answer_hospital_query(req.message, current_user)
    reply_text = ai_res["reply_text"] if isinstance(ai_res, dict) else str(ai_res)
    card_type = ai_res.get("card_type") if isinstance(ai_res, dict) else None
    cards = ai_res.get("cards", []) if isinstance(ai_res, dict) else []
    meta_json = json.dumps({"card_type": card_type, "cards": cards}) if (cards or card_type) else None

    asst_id = execute_insert(
        """INSERT INTO chat_messages (conversation_id, sender_role, message_text, timestamp, metadata_json)
           VALUES (?, 'assistant', ?, ?, ?)""",
        (conversation_id, reply_text, now_iso, meta_json)
    )

    # Update conversation updated_at
    execute_update("UPDATE chat_conversations SET updated_at = ? WHERE id = ?", (now_iso, conversation_id))

    return {
        "status": "success",
        "message": {
            "id": asst_id,
            "conversation_id": conversation_id,
            "sender_role": "assistant",
            "message_text": reply_text,
            "metadata_json": meta_json,
            "card_type": card_type,
            "cards": cards,
            "timestamp": now_iso
        }
    }

@router.put("/conversations/{conversation_id}/rename")
def rename_conversation(conversation_id: int, req: ConversationRenameRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    execute_update(
        "UPDATE chat_conversations SET title = ?, updated_at = ? WHERE id = ? AND user_id = ?",
        (req.title, datetime.now(timezone.utc).isoformat(), conversation_id, user_id)
    )
    return {"status": "success", "title": req.title}

@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    execute_update("DELETE FROM chat_conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id))
    return {"status": "success", "message": "Conversation thread deleted."}

@router.post("/ask-direct")
def ask_chatbot_direct(req: ChatMessageRequest, current_user: dict = Depends(get_current_user)):
    ai_res = HospitalAIService.answer_hospital_query(req.message, current_user)
    reply_text = ai_res["reply_text"] if isinstance(ai_res, dict) else str(ai_res)
    card_type = ai_res.get("card_type") if isinstance(ai_res, dict) else None
    cards = ai_res.get("cards", []) if isinstance(ai_res, dict) else []
    return {
        "status": "success",
        "message": {
            "sender_role": "assistant",
            "message_text": reply_text,
            "card_type": card_type,
            "cards": cards,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }

