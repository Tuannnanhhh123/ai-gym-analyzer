import time
import random
import base64
from io import BytesIO
from typing import Callable, Any

from PIL import Image


def retry_with_backoff(fn: Callable, max_retries: int = 5) -> Any:
    """Exponential back-off retry wrapper."""
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                wait = min((2 ** attempt) + random.uniform(0.5, 1.5), 35)
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Exceeded maximum retries.")


def pil_to_base64(img: Image.Image, fmt: str = "JPEG") -> str:
    """Convert PIL Image → base64 string."""
    buf = BytesIO()
    img.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode()


def resize_image(img: Image.Image, max_size: int = 1024) -> Image.Image:
    """Resize image keeping aspect ratio, max side = max_size px."""
    w, h = img.size
    if max(w, h) <= max_size:
        return img
    scale = max_size / max(w, h)
    return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)


def format_bmi(weight_kg: float, height_cm: float) -> dict:
    """Calculate BMI and return category."""
    h = height_cm / 100
    bmi = weight_kg / (h * h)
    if bmi < 18.5:
        cat, color = "Thiếu cân / Underweight", "#3498db"
    elif bmi < 25:
        cat, color = "Bình thường / Normal", "#2ecc71"
    elif bmi < 30:
        cat, color = "Thừa cân / Overweight", "#f39c12"
    else:
        cat, color = "Béo phì / Obese", "#e74c3c"
    return {"bmi": round(bmi, 1), "category": cat, "color": color}


def calc_tdee(weight: float, height: float, age: int,
              gender: str, activity: str) -> dict:
    """Harris-Benedict BMR + TDEE."""
    if gender == "Nam / Male":
        bmr = 88.362 + 13.397 * weight + 4.799 * height - 5.677 * age
    else:
        bmr = 447.593 + 9.247 * weight + 3.098 * height - 4.330 * age

    multipliers = {
        "Ít vận động / Sedentary":           1.2,
        "Nhẹ (1-3 ngày/tuần) / Light":       1.375,
        "Vừa (3-5 ngày/tuần) / Moderate":    1.55,
        "Nhiều (6-7 ngày/tuần) / Active":    1.725,
        "Rất nhiều / Very Active":            1.9,
    }
    tdee = bmr * multipliers.get(activity, 1.55)
    return {
        "bmr":  round(bmr),
        "tdee": round(tdee),
        "cut":  round(tdee - 500),   # giảm cân
        "bulk": round(tdee + 300),   # tăng cơ
    }