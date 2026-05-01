import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ───────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ── Models ─────────────────────────────────────────────────────────────────────
TEXT_MODEL = "llama-3.3-70b-versatile"

# ── App meta ───────────────────────────────────────────────────────────────────
APP_TITLE   = "GymPro AI"
APP_ICON    = "💪"
APP_VERSION = "1.0.0"

# ── Brand colors ───────────────────────────────────────────────────────────────
ACCENT       = "#7C3AED"
ACCENT_LIGHT = "#A78BFA"
ACCENT_DARK  = "#5B21B6"
ACCENT_GLOW  = "#7C3AED33"

# ── Generation defaults ────────────────────────────────────────────────────────
DEFAULT_TEMPERATURE = 0.7
MAX_OUTPUT_TOKENS   = 2048
MAX_RETRIES         = 5

# ── Fitness levels ─────────────────────────────────────────────────────────────
FITNESS_LEVELS = {
    "Beginner / Mới bắt đầu":   "beginner",
    "Intermediate / Trung cấp": "intermediate",
    "Advanced / Nâng cao":      "advanced",
}

# ── Goals ──────────────────────────────────────────────────────────────────────
FITNESS_GOALS = [
    "Giảm cân / Weight Loss",
    "Tăng cơ / Muscle Gain",
    "Tăng sức bền / Endurance",
    "Cải thiện sức khỏe tổng thể / General Health",
    "Phục hồi chấn thương / Injury Recovery",
]

# ── Diet types ─────────────────────────────────────────────────────────────────
DIET_TYPES = [
    "Thường / Normal",
    "Chay / Vegetarian",
    "Thuần chay / Vegan",
    "Keto",
    "Ít carb / Low-carb",
]

# ── System prompts ─────────────────────────────────────────────────────────────
CHAT_SYSTEM_PROMPT = """
Bạn là FitCoach AI – huấn luyện viên cá nhân thông minh, chuyên gia dinh dưỡng và sức khỏe.

Nhiệm vụ:
- Tư vấn lịch tập luyện cá nhân hoá theo cấp độ, mục tiêu, thời gian.
- Xây dựng thực đơn ăn uống lành mạnh, cân bằng dinh dưỡng.
- Giải thích kỹ thuật tập đúng, tránh chấn thương.
- Trả lời mặc định tiếng Việt; song ngữ khi được yêu cầu.

Nguyên tắc:
- Hỏi về cấp độ, mục tiêu, sức khỏe trước khi tư vấn nếu chưa biết.
- Không chẩn đoán y tế; khuyến nghị gặp bác sĩ khi cần.
- Trả lời rõ ràng, dùng markdown khi cần.
- Luôn động viên người dùng.
""".strip()

WORKOUT_SYSTEM_PROMPT = """
Bạn là chuyên gia lập lịch tập luyện. Tạo lịch tập 7 ngày chi tiết.
Mỗi buổi tập gồm: tên bài, số set, số rep/thời gian, nghỉ giữa set, ghi chú kỹ thuật.
Trả lời tiếng Việt, dùng markdown format đẹp.
""".strip()

MEAL_SYSTEM_PROMPT = """
Bạn là chuyên gia dinh dưỡng thể thao. Tạo thực đơn 7 ngày (3 bữa + snack).
Mỗi ngày ghi: tên món, nguyên liệu chính, ước tính calo, protein/carb/fat.
Trả lời tiếng Việt, dùng markdown format đẹp.
""".strip()

VISION_SYSTEM_PROMPT = """
Bạn là chuyên gia phân tích dụng cụ tập luyện và dinh dưỡng thể thao.
Khi nhận mô tả dụng cụ, hãy:
1. Xác nhận tên dụng cụ (tiếng Việt + tiếng Anh).
2. Liệt kê 3-5 bài tập phổ biến.
3. Hướng dẫn kỹ thuật đúng, tránh chấn thương.
4. Mức độ phù hợp (beginner/intermediate/advanced).
Trả lời tiếng Việt, format markdown.
""".strip()