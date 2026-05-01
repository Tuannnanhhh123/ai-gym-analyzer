from typing import List, Dict
from groq import Groq

from config import (
    GROQ_API_KEY, TEXT_MODEL,
    DEFAULT_TEMPERATURE, MAX_OUTPUT_TOKENS,
    CHAT_SYSTEM_PROMPT, WORKOUT_SYSTEM_PROMPT, MEAL_SYSTEM_PROMPT,
)
from utils.helpers import retry_with_backoff

# ── Singleton client ───────────────────────────────────────────────────────────
_groq_client: Groq | None = None

def _client() -> Groq:
    global _groq_client
    if _groq_client is None:
        if not GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY chưa được cấu hình. "
                "Thêm vào file .env: GROQ_API_KEY=your_key"
            )
        _groq_client = Groq(api_key=GROQ_API_KEY)
    return _groq_client


def _ask(system: str, messages: list, temp: float = DEFAULT_TEMPERATURE) -> str:
    """Gọi Groq API với retry + backoff."""
    client  = _client()
    payload = [{"role": "system", "content": system}] + messages

    def call():
        resp = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=payload,
            temperature=temp,
            max_tokens=MAX_OUTPUT_TOKENS,
        )
        return resp.choices[0].message.content.strip()

    return retry_with_backoff(call)


# ── Public API ─────────────────────────────────────────────────────────────────

def chat_response(history: List[Dict], user_message: str) -> str:
    """Trả lời chat với lịch sử hội thoại."""
    messages = [
        {"role": "user" if m["role"] == "user" else "assistant",
         "content": m["content"]}
        for m in history
    ]
    messages.append({"role": "user", "content": user_message})
    return _ask(CHAT_SYSTEM_PROMPT, messages)


def generate_workout_plan(
    level: str, goal: str, days_per_week: int,
    duration_min: int, equipment: str, notes: str,
) -> str:
    """Tạo lịch tập 7 ngày cá nhân hoá."""
    prompt = (
        f"Tạo lịch tập 7 ngày:\n"
        f"- Cấp độ: {level}\n"
        f"- Mục tiêu: {goal}\n"
        f"- Số buổi/tuần: {days_per_week}\n"
        f"- Thời gian/buổi: {duration_min} phút\n"
        f"- Dụng cụ: {equipment}\n"
        f"- Ghi chú: {notes or 'Không có'}\n\n"
        "Gồm warm-up, bài chính (tên, set, rep/thời gian, nghỉ), cool-down. "
        "Đánh dấu ngày nghỉ rõ ràng."
    )
    return _ask(WORKOUT_SYSTEM_PROMPT, [{"role": "user", "content": prompt}], temp=0.5)


def generate_meal_plan(
    goal: str, diet_type: str, calories: int,
    allergies: str, meals_per_day: int, notes: str,
) -> str:
    """Tạo thực đơn 7 ngày cá nhân hoá."""
    prompt = (
        f"Tạo thực đơn 7 ngày:\n"
        f"- Mục tiêu: {goal}\n"
        f"- Chế độ ăn: {diet_type}\n"
        f"- Calo/ngày: {calories} kcal\n"
        f"- Dị ứng: {allergies or 'Không có'}\n"
        f"- Số bữa/ngày: {meals_per_day}\n"
        f"- Ghi chú: {notes or 'Không có'}\n\n"
        "Mỗi ngày ghi rõ từng bữa, calo + macro (P/C/F). "
        "Thêm shopping list cuối tuần."
    )
    return _ask(MEAL_SYSTEM_PROMPT, [{"role": "user", "content": prompt}], temp=0.5)