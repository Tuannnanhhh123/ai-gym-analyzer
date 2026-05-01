"""
Preprocessing module — chuẩn hoá dữ liệu đầu vào người dùng.

Fix:
- clean_text() mạnh hơn: block nhiều pattern injection phổ biến
- Thêm validate_profile() để kiểm tra đầu vào trước khi transform
"""

import re
import numpy as np
import pandas as pd

# ── Phạm vi chuẩn hoá ─────────────────────────────────────────────────────────
WEIGHT_RANGE = (30.0, 200.0)
HEIGHT_RANGE = (100.0, 230.0)
AGE_RANGE    = (10, 90)

# ── Injection patterns cần block ──────────────────────────────────────────────
# Dùng 1 flag (?i) duy nhất bao toàn bộ pattern thay vì mỗi pattern 1 flag
_INJECTION_RE = re.compile(
    r'(?i)(?:'
    r'ignore\s+(?:previous|above|all)'
    r'|system\s*:'
    r'|you\s+are\s+now'
    r'|act\s+as'
    r'|forget\s+(?:everything|all)'
    r'|jailbreak'
    r'|DAN\b'
    r')'
    r'|<\|.*?\|>'      # không cần (?i) — không có chữ cái
    r'|#{3,}'
    r'|\[/?INST\]'
)


# ── 1. Min-max normalization ──────────────────────────────────────────────────
def normalize(value: float, min_val: float, max_val: float) -> float:
    if max_val == min_val:
        return 0.0
    return round((value - min_val) / (max_val - min_val), 4)


# ── 2. Validate profile ───────────────────────────────────────────────────────
def validate_profile(weight: float, height: float, age: int) -> list[str]:
    """Trả về list lỗi (rỗng = hợp lệ)."""
    errors = []
    if not (WEIGHT_RANGE[0] <= weight <= WEIGHT_RANGE[1]):
        errors.append(f"Cân nặng phải từ {WEIGHT_RANGE[0]}–{WEIGHT_RANGE[1]} kg")
    if not (HEIGHT_RANGE[0] <= height <= HEIGHT_RANGE[1]):
        errors.append(f"Chiều cao phải từ {HEIGHT_RANGE[0]}–{HEIGHT_RANGE[1]} cm")
    if not (AGE_RANGE[0] <= age <= AGE_RANGE[1]):
        errors.append(f"Tuổi phải từ {AGE_RANGE[0]}–{AGE_RANGE[1]}")
    return errors


# ── 3. Transform profile ──────────────────────────────────────────────────────
def transform_profile(weight: float, height: float, age: int,
                      gender: str, goal: str, level: str) -> dict:
    bmi = round(weight / ((height / 100) ** 2), 1)

    if bmi < 18.5:   bmi_cat = "thiếu cân"
    elif bmi < 25:   bmi_cat = "bình thường"
    elif bmi < 30:   bmi_cat = "thừa cân"
    else:            bmi_cat = "béo phì"

    if "Male" in gender or "Nam" in gender:
        bmr = 88.362 + 13.397 * weight + 4.799 * height - 5.677 * age
    else:
        bmr = 447.593 + 9.247 * weight + 3.098 * height - 4.330 * age

    tdee = round(bmr * 1.55)

    return {
        "raw": {
            "weight": weight, "height": height,
            "age": age, "gender": gender,
            "goal": goal, "level": level,
        },
        "normalized": {
            "weight_norm": normalize(weight, *WEIGHT_RANGE),
            "height_norm": normalize(height, *HEIGHT_RANGE),
            "age_norm":    normalize(age,    *AGE_RANGE),
        },
        "computed": {
            "bmi":           bmi,
            "bmi_category":  bmi_cat,
            "tdee_estimate": tdee,
        },
    }


def profile_to_prompt_context(profile_data: dict) -> str:
    r, c = profile_data["raw"], profile_data["computed"]
    return (
        f"Người dùng: {r['gender']}, {r['age']} tuổi, "
        f"{r['weight']}kg / {r['height']}cm, "
        f"BMI {c['bmi']} ({c['bmi_category']}), "
        f"TDEE ≈ {c['tdee_estimate']} kcal/ngày, "
        f"cấp độ: {r['level']}, mục tiêu: {r['goal']}."
    )


# ── 4. Clean text (chống prompt injection) ────────────────────────────────────
def clean_text(text: str, max_len: int = 500) -> str:
    """
    Làm sạch input trước khi đưa vào prompt:
    - Block các pattern injection phổ biến
    - Trim whitespace, giới hạn độ dài
    """
    text = text.strip()
    if _INJECTION_RE.search(text):
        # Thay vì crash, xoá phần nguy hiểm
        text = _INJECTION_RE.sub('', text).strip()
    text = re.sub(r'\s{3,}', '  ', text)
    return text[:max_len]


# ── 5. Build DataFrame & metrics ──────────────────────────────────────────────
def build_eval_dataframe(logs: list) -> pd.DataFrame:
    if not logs:
        return pd.DataFrame()
    df = pd.DataFrame(logs)
    df["correct_num"]  = df["correct"].astype(int)
    df["response_len"] = df["bot_answer"].str.len()
    return df


def compute_metrics(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"accuracy": None, "total": 0, "correct": 0, "avg_len": 0}
    return {
        "accuracy": round(float(df["correct_num"].mean()), 4),
        "total":    len(df),
        "correct":  int(df["correct_num"].sum()),
        "avg_len":  int(df["response_len"].mean()),
    }