"""
Evaluation module — đánh giá chất lượng phản hồi LLM theo bộ câu hỏi chuẩn.

Fix:
- Tách hoàn toàn logic business khỏi UI layer
- evaluate_batch() để UI chỉ cần gọi 1 hàm
- Thread-safe với exception handling tốt hơn
"""

from typing import Optional
import pandas as pd

from modules.preprocessing import build_eval_dataframe, compute_metrics

# ── Bộ câu hỏi chuẩn ──────────────────────────────────────────────────────────
EVAL_DATA = [
    {
        "category": "Lịch tập",
        "question":  "Bài tập nào tốt cho người mới bắt đầu tập gym?",
        "keywords":  ["squat", "push", "plank", "cơ bản", "beginner"],
        "expected":  "Các bài cơ bản như squat, push-up, plank phù hợp cho người mới.",
    },
    {
        "category": "Lịch tập",
        "question":  "Tôi nên tập mấy ngày một tuần để tăng cơ?",
        "keywords":  ["3", "4", "5", "tuần", "ngày"],
        "expected":  "Nên tập 3-5 ngày/tuần để tăng cơ hiệu quả.",
    },
    {
        "category": "Lịch tập",
        "question":  "Warm-up trước khi tập có cần thiết không?",
        "keywords":  ["cần", "khởi động", "chấn thương", "warm"],
        "expected":  "Warm-up rất cần thiết để tránh chấn thương.",
    },
    {
        "category": "Dinh dưỡng",
        "question":  "Protein quan trọng như thế nào với người tập gym?",
        "keywords":  ["protein", "cơ", "phục hồi", "g/kg"],
        "expected":  "Protein giúp phục hồi và xây dựng cơ bắp, cần 1.6-2.2g/kg.",
    },
    {
        "category": "Dinh dưỡng",
        "question":  "Tôi nên ăn gì trước khi tập?",
        "keywords":  ["carb", "tinh bột", "trước", "năng lượng"],
        "expected":  "Nên ăn carb phức và protein nhẹ 1-2 giờ trước khi tập.",
    },
    {
        "category": "Dinh dưỡng",
        "question":  "Người muốn giảm cân nên ăn bao nhiêu calo mỗi ngày?",
        "keywords":  ["deficit", "500", "tdee", "calo", "thiếu hụt"],
        "expected":  "Tạo deficit 300-500 kcal so với TDEE để giảm cân an toàn.",
    },
    {
        "category": "Dụng cụ",
        "question":  "Tạ đơn (dumbbell) có thể dùng để tập bài nào?",
        "keywords":  ["dumbbell", "tạ đơn", "curl", "press", "row"],
        "expected":  "Tạ đơn dùng được cho curl, press, row, lateral raise...",
    },
    {
        "category": "Dụng cụ",
        "question":  "Xà đơn giúp tập được những nhóm cơ nào?",
        "keywords":  ["lưng", "tay", "pull-up", "xà", "lat"],
        "expected":  "Xà đơn chủ yếu tập lưng (lat) và cơ tay thông qua pull-up.",
    },
    {
        "category": "Phục hồi",
        "question":  "Ngủ bao nhiêu tiếng là tốt nhất cho người tập thể thao?",
        "keywords":  ["7", "8", "giờ", "giấc ngủ", "phục hồi"],
        "expected":  "Nên ngủ 7-9 tiếng để phục hồi cơ bắp tốt nhất.",
    },
    {
        "category": "Phục hồi",
        "question":  "Đau cơ sau khi tập có bình thường không?",
        "keywords":  ["doms", "bình thường", "24", "48", "đau"],
        "expected":  "DOMS (đau cơ khởi phát chậm) sau 24-48h là bình thường.",
    },
]


# ── Keyword matching ───────────────────────────────────────────────────────────
def keyword_match(answer: str, keywords: list) -> bool:
    """True nếu câu trả lời chứa ít nhất 2 từ khoá."""
    answer_lower = answer.lower()
    matched = sum(1 for kw in keywords if kw.lower() in answer_lower)
    return matched >= min(2, len(keywords))


# ── Evaluate 1 item — tách khỏi UI ────────────────────────────────────────────
def evaluate_item(item: dict, answer: str) -> dict:
    """Chấm điểm 1 câu hỏi. Dùng bởi cả UI lẫn batch runner."""
    correct = keyword_match(answer, item["keywords"])
    return {
        "category":        item["category"],
        "question":        item["question"],
        "expected_answer": item["expected"],
        "bot_answer":      answer,
        "keywords":        ", ".join(item["keywords"]),
        "correct":         correct,
    }


# ── Batch evaluation (dùng cho run_full_evaluation) ───────────────────────────
def run_full_evaluation(category_filter: Optional[str] = None) -> dict:
    """
    Chạy toàn bộ test set qua LLM.
    Import chat_response ở đây để tránh circular import.
    """
    from modules.chat import chat_response

    data = EVAL_DATA
    if category_filter:
        data = [d for d in data if d["category"] == category_filter]

    logs = []
    for item in data:
        try:
            answer = chat_response([], item["question"])
        except Exception as e:
            answer = f"ERROR: {e}"
        logs.append(evaluate_item(item, answer))

    return _build_result(logs)


def _build_result(logs: list) -> dict:
    df      = build_eval_dataframe(logs)
    metrics = compute_metrics(df)
    metrics["loss"] = round(1.0 - (metrics["accuracy"] or 0), 4)

    by_cat = {}
    if not df.empty:
        by_cat = (
            df.groupby("category")["correct_num"]
            .mean().round(4).to_dict()
        )
    return {"df": df, "metrics": metrics, "by_cat": by_cat}


def evaluate_single(question: str, answer: str) -> Optional[dict]:
    """Tìm câu hỏi trong EVAL_DATA và chấm điểm."""
    for item in EVAL_DATA:
        if item["question"].strip().lower() == question.strip().lower():
            return evaluate_item(item, answer)
    return None


def get_categories() -> list:
    return sorted(set(d["category"] for d in EVAL_DATA))