"""
modules/image_analysis.py
─────────────────────────
Sử dụng YOLOv8 (.pt) cho 2 task:
  • gymmodel.pt   — nhận diện dụng cụ tập gym (classification)
  • foodmodel.pt  — nhận diện món ăn + ước tính calo (classification)

Fallback hoàn toàn sang LLM khi thiếu file model hoặc ultralytics chưa cài.
"""

from __future__ import annotations

import os
import io
import base64
import numpy as np
from PIL import Image

from modules.chat import _ask
from config import VISION_SYSTEM_PROMPT
from utils.helpers import retry_with_backoff

# ══════════════════════════════════════════════════════════════════════════════
# ĐƯỜNG DẪN MODEL
# ══════════════════════════════════════════════════════════════════════════════
_ROOT       = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GYM_MODEL_PATH  = os.path.join(_ROOT, "gymmodel.pt")
FOOD_MODEL_PATH = os.path.join(_ROOT, "foodmodel.pt")

# ══════════════════════════════════════════════════════════════════════════════
# THÔNG TIN DỤNG CỤ GYM
# ══════════════════════════════════════════════════════════════════════════════
CLASS_INFO_GYM: dict[str, dict] = {
    "benchPress":      {"vi": "Ghế tập ngực (Bench Press)",        "muscles": ["Cơ ngực", "Vai trước", "Tay sau"],        "level": "Intermediate",          "exercises": ["Bench Press", "Incline Press", "Decline Press", "Dumbbell Flyes", "Tricep Dips"]},
    "dumbBell":        {"vi": "Tạ đơn (Dumbbell)",                 "muscles": ["Toàn thân"],                               "level": "Beginner → Advanced",    "exercises": ["Bicep Curl", "Shoulder Press", "Lateral Raise", "Row", "Goblet Squat"]},
    "kettleBell":      {"vi": "Tạ ấm (Kettlebell)",                "muscles": ["Hông", "Đùi sau", "Lưng dưới", "Core"],   "level": "Intermediate",          "exercises": ["Kettlebell Swing", "Turkish Get-Up", "Clean & Press", "Goblet Squat", "Snatch"]},
    "pullBar":         {"vi": "Xà đơn (Pull-up Bar)",              "muscles": ["Lưng rộng", "Tay trước", "Lưng giữa"],    "level": "Intermediate",          "exercises": ["Pull-up", "Chin-up", "Hanging Knee Raise", "L-sit", "Negative Pull-up"]},
    "treadMill":       {"vi": "Máy chạy bộ (Treadmill)",           "muscles": ["Đùi", "Đùi sau", "Bắp chân", "Tim mạch"], "level": "Beginner → Advanced",   "exercises": ["Jogging", "Running", "HIIT", "Incline Walk", "Sprint Intervals"]},
    "resistanceBand":  {"vi": "Dây kháng lực (Resistance Band)",   "muscles": ["Toàn thân"],                               "level": "Beginner",              "exercises": ["Banded Squat", "Banded Row", "Lateral Walk", "Chest Press", "External Rotation"]},
    "foamRoller":      {"vi": "Con lăn xốp (Foam Roller)",         "muscles": ["Phục hồi cơ toàn thân"],                  "level": "Beginner",              "exercises": ["IT Band Roll", "Quad Roll", "Upper Back Roll", "Calf Roll", "Hip Flexor Roll"]},
    "jumpRope":        {"vi": "Dây nhảy (Jump Rope)",              "muscles": ["Bắp chân", "Tim mạch", "Phối hợp"],       "level": "Beginner → Advanced",   "exercises": ["Basic Jump", "Double Under", "Alternating Foot", "High Knees", "Cross Jump"]},
    "medicineBall":    {"vi": "Bóng y tế (Medicine Ball)",         "muscles": ["Core", "Toàn thân"],                      "level": "Intermediate",          "exercises": ["Slam", "Wall Ball", "Russian Twist", "Chest Pass", "Overhead Toss"]},
    "battleRope":      {"vi": "Dây chiến đấu (Battle Rope)",       "muscles": ["Vai", "Lưng", "Core", "Tim mạch"],        "level": "Intermediate",          "exercises": ["Alternating Waves", "Double Waves", "Slam", "Spiral", "Side-to-Side"]},
    "cableMachine":    {"vi": "Máy cáp (Cable Machine)",           "muscles": ["Toàn thân"],                               "level": "Intermediate",          "exercises": ["Cable Fly", "Tricep Pushdown", "Cable Row", "Face Pull", "Lat Pulldown"]},
    "legPress":        {"vi": "Máy ép đùi (Leg Press)",            "muscles": ["Đùi trước", "Mông", "Đùi sau"],           "level": "Beginner → Intermediate","exercises": ["Standard Leg Press", "Narrow Stance", "Wide Stance", "Single Leg", "Calf Press"]},
    "smithMachine":    {"vi": "Máy Smith (Smith Machine)",         "muscles": ["Toàn thân"],                               "level": "Beginner → Advanced",   "exercises": ["Smith Squat", "Smith Bench", "Smith Row", "Smith Deadlift", "Smith Lunge"]},
    "rowingMachine":   {"vi": "Máy chèo thuyền (Rowing Machine)",  "muscles": ["Lưng", "Đùi", "Core", "Tim mạch"],        "level": "Beginner → Advanced",   "exercises": ["Steady State Row", "HIIT Row", "Pyramid Row", "Interval Training", "Endurance Row"]},
    "elliptical":      {"vi": "Máy đạp elip (Elliptical)",         "muscles": ["Toàn thân", "Tim mạch"],                  "level": "Beginner",              "exercises": ["Forward Stride", "Reverse Stride", "High Incline", "HIIT Interval", "Arm Focus"]},
    "yogaMat":         {"vi": "Thảm yoga (Yoga Mat)",              "muscles": ["Linh hoạt", "Core", "Thăng bằng"],        "level": "Beginner",              "exercises": ["Plank", "Downward Dog", "Warrior Pose", "Core Work", "Stretching"]},
    "stabilityBall":   {"vi": "Bóng thăng bằng (Stability Ball)",  "muscles": ["Core", "Lưng", "Thăng bằng"],             "level": "Beginner → Intermediate","exercises": ["Ball Crunch", "Ball Plank", "Wall Squat", "Back Extension", "Pike"]},
    "pulldownMachine": {"vi": "Máy kéo xà (Lat Pulldown)",         "muscles": ["Lưng rộng", "Tay trước", "Lưng giữa"],    "level": "Beginner → Intermediate","exercises": ["Wide Grip Pulldown", "Close Grip", "Reverse Grip", "Single Arm", "Behind Neck"]},
    "pecDeck":         {"vi": "Máy tập ngực (Pec Deck)",           "muscles": ["Cơ ngực", "Vai trước"],                   "level": "Beginner → Intermediate","exercises": ["Pec Deck Fly", "Reverse Fly", "Single Arm Fly", "Partial Rep", "Isometric Hold"]},
    "weightPlate":     {"vi": "Đĩa tạ (Weight Plate)",             "muscles": ["Toàn thân"],                               "level": "Intermediate",          "exercises": ["Plate Front Raise", "Plate Squat", "Plate Row", "Overhead Press", "Russian Twist"]},
    "barbellRack":     {"vi": "Giá đỡ tạ đòn (Barbell Rack)",      "muscles": ["Toàn thân"],                               "level": "Intermediate → Advanced","exercises": ["Back Squat", "Barbell Bench", "Barbell Row", "Deadlift", "Overhead Press"]},
    "dipStation":      {"vi": "Giá chống đẩy (Dip Station)",       "muscles": ["Tay sau", "Ngực", "Vai"],                 "level": "Intermediate",          "exercises": ["Tricep Dips", "Chest Dips", "L-sit", "Knee Raises", "Straight Bar Dips"]},
}

# ══════════════════════════════════════════════════════════════════════════════
# THÔNG TIN DINH DƯỠNG MÓN ĂN (calo ước tính / 100g hoặc / khẩu phần thông thường)
# ══════════════════════════════════════════════════════════════════════════════
FOOD_NUTRITION: dict[str, dict] = {
    # Cơm & tinh bột
    "rice":          {"vi": "Cơm trắng",           "cal_per_100g": 130, "protein": 2.7, "carb": 28,  "fat": 0.3, "gym_rating": "⭐⭐⭐",   "note": "Nguồn carb tốt, ăn trước/sau tập"},
    "brown_rice":    {"vi": "Cơm gạo lứt",         "cal_per_100g": 123, "protein": 2.6, "carb": 26,  "fat": 0.9, "gym_rating": "⭐⭐⭐⭐",  "note": "Chỉ số GI thấp, giàu chất xơ"},
    "bread":         {"vi": "Bánh mì",              "cal_per_100g": 265, "protein": 9,   "carb": 49,  "fat": 3.2, "gym_rating": "⭐⭐⭐",   "note": "Carb nhanh, tốt trước tập"},
    "noodles":       {"vi": "Mì/Bún/Phở",          "cal_per_100g": 138, "protein": 4.5, "carb": 28,  "fat": 0.5, "gym_rating": "⭐⭐⭐",   "note": "Carb trung bình, dễ tiêu"},
    "oats":          {"vi": "Yến mạch",             "cal_per_100g": 389, "protein": 17,  "carb": 66,  "fat": 7,   "gym_rating": "⭐⭐⭐⭐⭐", "note": "Bữa sáng lý tưởng, no lâu"},
    "sweet_potato":  {"vi": "Khoai lang",           "cal_per_100g": 86,  "protein": 1.6, "carb": 20,  "fat": 0.1, "gym_rating": "⭐⭐⭐⭐⭐", "note": "Carb chất lượng cao, giàu vitamin"},
    # Protein
    "chicken":       {"vi": "Ức gà",               "cal_per_100g": 165, "protein": 31,  "carb": 0,   "fat": 3.6, "gym_rating": "⭐⭐⭐⭐⭐", "note": "Protein nạc #1 cho gym"},
    "beef":          {"vi": "Thịt bò",              "cal_per_100g": 250, "protein": 26,  "carb": 0,   "fat": 15,  "gym_rating": "⭐⭐⭐⭐",  "note": "Protein + creatine tự nhiên"},
    "pork":          {"vi": "Thịt heo",             "cal_per_100g": 242, "protein": 27,  "carb": 0,   "fat": 14,  "gym_rating": "⭐⭐⭐",   "note": "Chọn phần nạc để tối ưu"},
    "egg":           {"vi": "Trứng gà",             "cal_per_100g": 155, "protein": 13,  "carb": 1.1, "fat": 11,  "gym_rating": "⭐⭐⭐⭐⭐", "note": "Protein hoàn chỉnh, giá rẻ"},
    "fish":          {"vi": "Cá",                   "cal_per_100g": 136, "protein": 20,  "carb": 0,   "fat": 6,   "gym_rating": "⭐⭐⭐⭐⭐", "note": "Omega-3 + protein nạc"},
    "shrimp":        {"vi": "Tôm",                  "cal_per_100g": 99,  "protein": 24,  "carb": 0.2, "fat": 0.3, "gym_rating": "⭐⭐⭐⭐⭐", "note": "Protein cao, calo thấp"},
    "tofu":          {"vi": "Đậu hũ",              "cal_per_100g": 76,  "protein": 8,   "carb": 1.9, "fat": 4.8, "gym_rating": "⭐⭐⭐⭐",  "note": "Protein thực vật tốt"},
    # Rau củ
    "salad":         {"vi": "Salad rau",            "cal_per_100g": 20,  "protein": 1.5, "carb": 3,   "fat": 0.2, "gym_rating": "⭐⭐⭐⭐",  "note": "Vitamin & khoáng chất thiết yếu"},
    "broccoli":      {"vi": "Bông cải xanh",        "cal_per_100g": 34,  "protein": 2.8, "carb": 7,   "fat": 0.4, "gym_rating": "⭐⭐⭐⭐⭐", "note": "Siêu thực phẩm cho gym"},
    "vegetables":    {"vi": "Rau củ quả",           "cal_per_100g": 30,  "protein": 2,   "carb": 6,   "fat": 0.3, "gym_rating": "⭐⭐⭐⭐",  "note": "Đa dạng màu sắc, giàu vi chất"},
    # Trái cây
    "banana":        {"vi": "Chuối",                "cal_per_100g": 89,  "protein": 1.1, "carb": 23,  "fat": 0.3, "gym_rating": "⭐⭐⭐⭐⭐", "note": "Snack trước tập lý tưởng"},
    "fruit":         {"vi": "Trái cây",             "cal_per_100g": 60,  "protein": 0.8, "carb": 15,  "fat": 0.2, "gym_rating": "⭐⭐⭐⭐",  "note": "Vitamin C + chất chống oxy hoá"},
    # Fast food / chế biến
    "pizza":         {"vi": "Pizza",                "cal_per_100g": 266, "protein": 11,  "carb": 33,  "fat": 10,  "gym_rating": "⭐⭐",     "note": "Calo cao, hạn chế khi giảm cân"},
    "burger":        {"vi": "Hamburger",            "cal_per_100g": 295, "protein": 17,  "carb": 24,  "fat": 14,  "gym_rating": "⭐⭐",     "note": "Ăn sau tập nặng để refeed"},
    "fried_food":    {"vi": "Đồ chiên xào",        "cal_per_100g": 320, "protein": 12,  "carb": 28,  "fat": 18,  "gym_rating": "⭐",       "note": "Hạn chế tối đa khi giảm mỡ"},
    # Dairy / bổ sung
    "yogurt":        {"vi": "Sữa chua",             "cal_per_100g": 59,  "protein": 10,  "carb": 3.6, "fat": 0.4, "gym_rating": "⭐⭐⭐⭐⭐", "note": "Protein + probiotic tuyệt vời"},
    "milk":          {"vi": "Sữa",                  "cal_per_100g": 61,  "protein": 3.2, "carb": 4.8, "fat": 3.3, "gym_rating": "⭐⭐⭐⭐",  "note": "Whey tự nhiên sau tập"},
    "nuts":          {"vi": "Hạt các loại",         "cal_per_100g": 580, "protein": 20,  "carb": 20,  "fat": 50,  "gym_rating": "⭐⭐⭐⭐",  "note": "Chất béo tốt + protein, ăn ít"},
    "protein_shake": {"vi": "Protein shake",        "cal_per_100g": 120, "protein": 25,  "carb": 5,   "fat": 2,   "gym_rating": "⭐⭐⭐⭐⭐", "note": "Bổ sung protein sau tập nhanh"},
    # Default
    "food":          {"vi": "Món ăn",               "cal_per_100g": 150, "protein": 10,  "carb": 20,  "fat": 5,   "gym_rating": "⭐⭐⭐",   "note": "Phân tích chi tiết bên dưới"},
}


# ══════════════════════════════════════════════════════════════════════════════
# MODEL CACHE
# ══════════════════════════════════════════════════════════════════════════════
_gym_model_cache  = None
_food_model_cache = None
_gym_unavail      = False
_food_unavail     = False


def _load_yolo(path: str, tag: str):
    """Load YOLOv8 model, trả về None nếu không có."""
    if not os.path.exists(path):
        return None
    try:
        from ultralytics import YOLO
        model = YOLO(path)
        print(f"[image_analysis] ✅ Loaded {tag}: {path}")
        return model
    except Exception as e:
        print(f"[image_analysis] ❌ Cannot load {tag}: {e}")
        return None


def _get_gym_model():
    global _gym_model_cache, _gym_unavail
    if _gym_model_cache is not None:
        return _gym_model_cache
    if _gym_unavail:
        return None
    _gym_model_cache = _load_yolo(GYM_MODEL_PATH, "gymmodel")
    if _gym_model_cache is None:
        _gym_unavail = True
    return _gym_model_cache


def _get_food_model():
    global _food_model_cache, _food_unavail
    if _food_model_cache is not None:
        return _food_model_cache
    if _food_unavail:
        return None
    _food_model_cache = _load_yolo(FOOD_MODEL_PATH, "foodmodel")
    if _food_model_cache is None:
        _food_unavail = True
    return _food_model_cache


# ══════════════════════════════════════════════════════════════════════════════
# PIL → base64 (để truyền vào YOLO predict)
# ══════════════════════════════════════════════════════════════════════════════
def _pil_to_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG")
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# PREDICT — GYM EQUIPMENT (gymmodel.pt)
# ══════════════════════════════════════════════════════════════════════════════
def predict_equipment(img: Image.Image) -> dict:
    """
    Chạy gymmodel.pt để nhận diện dụng cụ.
    Trả về dict chuẩn hoá, fallback=True nếu không có model.
    """
    model = _get_gym_model()

    if model is None:
        return {"class_name": None, "confidence": 0.0,
                "all_probs": {}, "fallback": True, "source": "llm"}

    try:
        img_rgb = img.convert("RGB")
        results = model.predict(source=img_rgb, verbose=False, task="classify")
        res     = results[0]

        # YOLOv8 classify: res.probs.top5, res.probs.top5conf, res.names
        probs_obj = res.probs
        names     = res.names  # {0: "benchPress", ...}

        top_idx  = int(probs_obj.top1)
        top_cls  = names[top_idx]
        top_conf = float(probs_obj.top1conf)

        # Tất cả xác suất
        all_probs = {}
        raw = probs_obj.data.cpu().numpy() if hasattr(probs_obj.data, "cpu") else np.array(probs_obj.data)
        for i, prob in enumerate(raw):
            all_probs[names[i]] = float(prob)

        return {
            "class_name": top_cls,
            "confidence": top_conf,
            "all_probs":  all_probs,
            "fallback":   False,
            "source":     "gymmodel.pt",
        }

    except Exception as e:
        print(f"[predict_equipment] Error: {e}")
        return {"class_name": None, "confidence": 0.0,
                "all_probs": {}, "fallback": True, "source": "llm", "error": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# PREDICT — FOOD (foodmodel.pt)
# ══════════════════════════════════════════════════════════════════════════════
def predict_food(img: Image.Image) -> dict:
    """
    Chạy foodmodel.pt để nhận diện món ăn.
    Trả về dict với nutrition info.
    """
    model = _get_food_model()

    if model is None:
        return {"class_name": None, "confidence": 0.0,
                "all_probs": {}, "fallback": True, "source": "llm"}

    try:
        img_rgb = img.convert("RGB")
        results = model.predict(source=img_rgb, verbose=False, task="classify")
        res     = results[0]

        probs_obj = res.probs
        names     = res.names

        top_idx  = int(probs_obj.top1)
        top_cls  = names[top_idx]
        top_conf = float(probs_obj.top1conf)

        all_probs = {}
        raw = probs_obj.data.cpu().numpy() if hasattr(probs_obj.data, "cpu") else np.array(probs_obj.data)
        for i, prob in enumerate(raw):
            all_probs[names[i]] = float(prob)

        # Lấy nutrition info
        nutrition = FOOD_NUTRITION.get(top_cls, FOOD_NUTRITION["food"])

        return {
            "class_name": top_cls,
            "confidence": top_conf,
            "all_probs":  all_probs,
            "nutrition":  nutrition,
            "fallback":   False,
            "source":     "foodmodel.pt",
        }

    except Exception as e:
        print(f"[predict_food] Error: {e}")
        return {"class_name": None, "confidence": 0.0,
                "all_probs": {}, "fallback": True, "source": "llm", "error": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# BUILD PROMPT — EQUIPMENT
# ══════════════════════════════════════════════════════════════════════════════
def _build_gym_prompt(pred: dict, user_note: str = "") -> str:
    if pred.get("fallback"):
        base = (
            "Người dùng upload ảnh dụng cụ tập gym. Model gymmodel.pt chưa khả dụng. "
            "Hãy quan sát và mô tả dụng cụ trong ảnh (nếu có thể), "
            "sau đó tư vấn cách sử dụng an toàn và hiệu quả.\n"
        )
        return base + (f"\nGhi chú người dùng: {user_note}" if user_note else "")

    cls  = pred["class_name"]
    info = CLASS_INFO_GYM.get(cls, {"vi": cls, "muscles": ["Toàn thân"], "level": "N/A", "exercises": []})
    conf_pct = pred["confidence"] * 100

    exercises_str = "\n".join(f"  • {e}" for e in info["exercises"])
    muscles_str   = ", ".join(info["muscles"])

    return (
        f"gymmodel.pt nhận diện dụng cụ: **{info['vi']}** (độ chính xác: {conf_pct:.1f}%)\n"
        f"Nguồn model: {pred.get('source','gymmodel.pt')}\n\n"
        f"Nhóm cơ chính: {muscles_str}\n"
        f"Cấp độ phù hợp: {info['level']}\n"
        f"Bài tập phổ biến:\n{exercises_str}\n"
        + (f"\nGhi chú người dùng: {user_note}\n" if user_note else "")
        + "\n---\n"
        "Hãy viết phân tích chi tiết bằng **Markdown tiếng Việt** gồm:\n"
        "1. **Tên & công dụng** dụng cụ\n"
        "2. **Hướng dẫn kỹ thuật** từng bài tập (form chuẩn, breathing)\n"
        "3. **Lỗi thường gặp** và cách tránh\n"
        "4. **Lộ trình** cho người mới bắt đầu\n"
        "5. **Tips nâng cao** cho người có kinh nghiệm\n"
        "Viết súc tích, dùng bullet points và emoji cho sinh động."
    )


# ══════════════════════════════════════════════════════════════════════════════
# BUILD PROMPT — FOOD
# ══════════════════════════════════════════════════════════════════════════════
def _build_food_prompt(pred: dict, serving_g: int = 200) -> str:
    if pred.get("fallback"):
        return (
            "Người dùng upload ảnh món ăn. Model foodmodel.pt chưa khả dụng. "
            "Hãy quan sát ảnh, xác định món ăn, ước tính calo và macro "
            "(Protein/Carb/Fat) cho 1 khẩu phần thông thường. "
            "Đánh giá mức độ phù hợp cho người tập gym và gợi ý điều chỉnh. "
            "Trả lời tiếng Việt, format markdown đẹp với bảng dinh dưỡng."
        )

    cls       = pred["class_name"]
    nut       = pred.get("nutrition", FOOD_NUTRITION.get(cls, FOOD_NUTRITION["food"]))
    conf_pct  = pred["confidence"] * 100
    food_name = nut["vi"]

    # Tính calo theo khẩu phần
    cal_serving  = int(nut["cal_per_100g"] * serving_g / 100)
    prot_serving = round(nut["protein"]    * serving_g / 100, 1)
    carb_serving = round(nut["carb"]       * serving_g / 100, 1)
    fat_serving  = round(nut["fat"]        * serving_g / 100, 1)

    return (
        f"foodmodel.pt nhận diện: **{food_name}** (độ chính xác: {conf_pct:.1f}%)\n"
        f"Nguồn model: {pred.get('source','foodmodel.pt')}\n\n"
        f"**Ước tính dinh dưỡng cho {serving_g}g:**\n"
        f"- Calo: {cal_serving} kcal\n"
        f"- Protein: {prot_serving}g\n"
        f"- Carbohydrate: {carb_serving}g\n"
        f"- Chất béo: {fat_serving}g\n"
        f"- Phù hợp gym: {nut['gym_rating']}\n"
        f"- Ghi chú nhanh: {nut['note']}\n\n"
        "---\n"
        "Hãy viết phân tích dinh dưỡng chi tiết bằng **Markdown tiếng Việt** gồm:\n"
        "1. **Bảng dinh dưỡng** (per 100g và per khẩu phần)\n"
        "2. **Đánh giá** mức độ phù hợp với từng mục tiêu (giảm cân / tăng cơ / bền sức)\n"
        "3. **Thời điểm tốt nhất** để ăn (trước/sau tập, buổi sáng…)\n"
        "4. **Gợi ý kết hợp** thực phẩm để tăng giá trị dinh dưỡng\n"
        "5. **Lưu ý** nếu ăn quá nhiều\n"
        "Dùng emoji và bảng markdown cho sinh động, dễ đọc."
    )


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════
def analyze_equipment_image(img: Image.Image, user_note: str = "") -> tuple[dict, str]:
    """
    Nhận diện dụng cụ gym bằng gymmodel.pt + LLM tư vấn.
    Returns: (pred_dict, detail_markdown)
    """
    pred   = predict_equipment(img)
    prompt = _build_gym_prompt(pred, user_note)
    detail = retry_with_backoff(
        lambda: _ask(VISION_SYSTEM_PROMPT,
                     [{"role": "user", "content": prompt}], temp=0.5)
    )
    return pred, detail


def analyze_food_image(img: Image.Image, serving_g: int = 200) -> tuple[dict, str]:
    """
    Nhận diện món ăn bằng foodmodel.pt + LLM phân tích dinh dưỡng.
    Returns: (pred_dict, detail_markdown)
    """
    pred   = predict_food(img)
    prompt = _build_food_prompt(pred, serving_g)
    detail = retry_with_backoff(
        lambda: _ask(
            "Bạn là chuyên gia dinh dưỡng thể thao. "
            "Phân tích chi tiết, trả lời tiếng Việt, dùng markdown + bảng.",
            [{"role": "user", "content": prompt}], temp=0.4
        )
    )
    return pred, detail


def model_status() -> dict:
    """Kiểm tra trạng thái 2 model."""
    return {
        "gymmodel":  {"path": GYM_MODEL_PATH,  "available": os.path.exists(GYM_MODEL_PATH)},
        "foodmodel": {"path": FOOD_MODEL_PATH, "available": os.path.exists(FOOD_MODEL_PATH)},
    }