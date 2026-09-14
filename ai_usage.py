import json
import os
from pathlib import Path

AI_QUESTION_LIMIT = 3
AI_USAGE_FILE = Path(os.getenv("AI_USAGE_FILE", "data/ai_usage.json"))

SUPABASE_URL = os.getenv("SUPABASE_URL") or ""
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or ""
_supabase = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as exc:
        print(f"SUPABASE INIT ERROR [{type(exc).__name__}]: {exc}")


def _load_usage():
    try:
        if not AI_USAGE_FILE.exists():
            return {}
        with AI_USAGE_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_usage(data):
    AI_USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = AI_USAGE_FILE.with_suffix(".tmp")
    with temp_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    temp_file.replace(AI_USAGE_FILE)


def _get_supabase_count(user_id: int) -> int:
    result = (
        _supabase.table("ai_usage")
        .select("question_count")
        .eq("telegram_user_id", user_id)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    if not rows:
        return 0
    try:
        return int(rows[0].get("question_count", 0))
    except (TypeError, ValueError):
        return 0


def get_ai_question_count(user_id: int) -> int:
    if _supabase is not None:
        try:
            return _get_supabase_count(user_id)
        except Exception as exc:
            print(f"SUPABASE AI USAGE READ ERROR [{type(exc).__name__}]: {exc}")

    data = _load_usage()
    try:
        return int(data.get(str(user_id), 0))
    except (TypeError, ValueError):
        return 0


def get_ai_questions_remaining(user_id: int) -> int:
    return max(0, AI_QUESTION_LIMIT - get_ai_question_count(user_id))


def can_ask_ai(user_id: int) -> bool:
    return get_ai_question_count(user_id) < AI_QUESTION_LIMIT


def _consume_supabase_question(user_id: int) -> int:
    result = _supabase.rpc(
        "consume_ai_question",
        {
            "p_telegram_user_id": user_id,
            "p_limit": AI_QUESTION_LIMIT,
        },
    ).execute()
    try:
        return max(0, int(result.data))
    except (TypeError, ValueError):
        return 0


def consume_ai_question(user_id: int) -> int:
    if _supabase is not None:
        try:
            return _consume_supabase_question(user_id)
        except Exception as exc:
            print(f"SUPABASE AI USAGE WRITE ERROR [{type(exc).__name__}]: {exc}")

    data = _load_usage()
    key = str(user_id)
    try:
        current = int(data.get(key, 0))
    except (TypeError, ValueError):
        current = 0

    if current >= AI_QUESTION_LIMIT:
        return 0

    data[key] = current + 1
    _save_usage(data)
    return AI_QUESTION_LIMIT - data[key]
