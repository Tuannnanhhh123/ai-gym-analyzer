"""
ui/sidebar.py  —  Sidebar chứa TẤT CẢ chức năng:
  👤 Hồ sơ  |  🗓️ Lịch tập  |  🥗 Thực đơn
  📈 Tiến độ  |  📊 Đánh giá  |  📸 Ảnh
"""

import streamlit as st
import base64, os, datetime
import plotly.graph_objects as go
from PIL import Image

from config import FITNESS_LEVELS, FITNESS_GOALS, DIET_TYPES
from utils.helpers import format_bmi, calc_tdee
from modules.image_analysis import analyze_equipment_image, analyze_food_image
from modules.chat import generate_workout_plan, generate_meal_plan
from modules.preprocessing import clean_text, build_eval_dataframe, compute_metrics
from modules.evaluation import EVAL_DATA, evaluate_item

C = {
    "bg3":"#111111","bg4":"#161616","border":"#2a2a2a","border2":"#3a3a3a",
    "text":"#f0f0f0","text_sub":"#c0c0c0","muted":"#707070",
    "accent":"#8b5cf6","accent_l":"#a78bfa","accent_d":"#6d28d9",
    "success":"#22c55e","warning":"#f59e0b","danger":"#ef4444",
}

_DP = {
    "name":"User","age":25,"gender":"Nam / Male","weight":70.0,"height":170.0,
    "activity":"Vừa (3-5 ngày/tuần) / Moderate",
    "level":list(FITNESS_LEVELS.keys())[0],"goal":FITNESS_GOALS[0],"diet":DIET_TYPES[0],
}

def _init(k, v):
    if k not in st.session_state: st.session_state[k] = v

def _logo(path="assets/gym-creative-icon-free-vector.webp"):
    if not os.path.exists(path): return ""
    with open(path,"rb") as f: return base64.b64encode(f.read()).decode()

def _sec(title):
    st.markdown(
        f"<div style='font-size:.7rem;font-weight:700;color:{C['accent_l']};"
        f"text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px'>{title}</div>",
        unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — HỒ SƠ
# ══════════════════════════════════════════════════════════════════════════════
def _tab_profile():
    _sec("Hồ sơ cá nhân")
    p = st.session_state.get("saved_profile", {})
    with st.form("pf"):
        name = st.text_input("Tên", value=p.get("name",""), placeholder="Tên của bạn")
        c1,c2 = st.columns(2)
        age    = c1.number_input("Tuổi", 10, 90, int(p.get("age",25)))
        gender = c2.selectbox("Giới tính",["Nam / Male","Nữ / Female"],
                              index=0 if p.get("gender","Nam / Male")!="Nữ / Female" else 1)
        c3,c4 = st.columns(2)
        weight = c3.number_input("Cân nặng (kg)",30.0,200.0,float(p.get("weight",70.0)),0.5)
        height = c4.number_input("Chiều cao (cm)",100.0,230.0,float(p.get("height",170.0)),0.5)
        activity = st.selectbox("Mức hoạt động",[
            "Ít vận động / Sedentary","Nhẹ (1-3 ngày/tuần) / Light",
            "Vừa (3-5 ngày/tuần) / Moderate","Nhiều (6-7 ngày/tuần) / Active",
            "Rất nhiều / Very Active"], index=2)
        c5,c6 = st.columns(2)
        level = c5.selectbox("Cấp độ", list(FITNESS_LEVELS.keys()))
        goal  = c6.selectbox("Mục tiêu", FITNESS_GOALS)
        diet  = st.selectbox("Chế độ ăn", DIET_TYPES)
        ok = st.form_submit_button("💾 Lưu hồ sơ", use_container_width=True)
    if ok:
        st.session_state.saved_profile = dict(
            name=name,age=age,gender=gender,weight=weight,height=height,
            activity=activity,level=level,goal=goal,diet=diet)
        st.success("✅ Đã lưu!")
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — LỊCH TẬP
# ══════════════════════════════════════════════════════════════════════════════
def _tab_workout(p):
    _sec("Lịch tập 7 ngày")
    _init("workout_result","")
    with st.form("wk"):
        c1,c2 = st.columns(2)
        level = c1.selectbox("Cấp độ", list(FITNESS_LEVELS.keys()),
                             index=list(FITNESS_LEVELS.keys()).index(p["level"]))
        goal  = c2.selectbox("Mục tiêu", FITNESS_GOALS,
                             index=FITNESS_GOALS.index(p["goal"]) if p["goal"] in FITNESS_GOALS else 0)
        c3,c4 = st.columns(2)
        days  = c3.slider("Buổi/tuần",2,7,4)
        dur   = c4.slider("Phút/buổi",20,120,60,5)
        eq = st.multiselect("Dụng cụ sẵn có",[
            "Tạ đơn / Dumbbells","Tạ đòn / Barbell","Xà đơn / Pull-up bar",
            "Dây kháng lực","Máy cable","Thảm tập / Mat","Bodyweight only"],
            default=["Tạ đơn / Dumbbells","Thảm tập / Mat"])
        notes = st.text_area("Ghi chú",height=55,placeholder="VD: Đau đầu gối…")
        ok = st.form_submit_button("🚀 Tạo lịch tập", use_container_width=True)
    if ok:
        with st.spinner("Đang tạo lịch tập…"):
            try:
                st.session_state.workout_result = generate_workout_plan(
                    level,goal,days,dur,", ".join(eq) if eq else "Bodyweight",clean_text(notes))
            except Exception as e:
                st.session_state.workout_result = f"❌ {e}"
    if st.session_state.workout_result:
        st.divider()
        st.markdown(st.session_state.workout_result)
        st.download_button("📥 Tải .md", data=st.session_state.workout_result,
                           file_name="lichTap.md", mime="text/markdown",
                           use_container_width=True, key="dl_wk")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — THỰC ĐƠN
# ══════════════════════════════════════════════════════════════════════════════
def _tab_meal(p):
    _sec("Thực đơn 7 ngày")
    _init("meal_result","")
    tdee = p.get("tdee",{"cut":1700,"bulk":2500,"tdee":2000})
    with st.form("ml"):
        c1,c2 = st.columns(2)
        goal = c1.selectbox("Mục tiêu", FITNESS_GOALS,
                            index=FITNESS_GOALS.index(p["goal"]) if p["goal"] in FITNESS_GOALS else 0)
        diet = c2.selectbox("Chế độ ăn", DIET_TYPES)
        c3,c4 = st.columns(2)
        def_c = tdee["cut"] if "Giảm" in goal else tdee["bulk"] if "Tăng cơ" in goal else tdee["tdee"]
        cal   = c3.number_input("Calo/ngày",500,5000,int(def_c),50)
        bua   = c4.selectbox("Số bữa/ngày",[3,4,5,6])
        allg  = st.text_input("Dị ứng",placeholder="VD: hải sản…")
        notes = st.text_area("Ghi chú",height=50,placeholder="VD: món dễ nấu…")
        ok = st.form_submit_button("🍽️ Tạo thực đơn", use_container_width=True)
    if ok:
        with st.spinner("Đang tạo thực đơn…"):
            try:
                st.session_state.meal_result = generate_meal_plan(
                    goal,diet,cal,clean_text(allg),bua,clean_text(notes))
            except Exception as e:
                st.session_state.meal_result = f"❌ {e}"
    if st.session_state.meal_result:
        st.divider()
        st.markdown(st.session_state.meal_result)
        st.download_button("📥 Tải .md", data=st.session_state.meal_result,
                           file_name="thucDon.md", mime="text/markdown",
                           use_container_width=True, key="dl_ml")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — TIẾN ĐỘ
# ══════════════════════════════════════════════════════════════════════════════
def _tab_progress(p):
    _sec("Theo dõi tiến độ")
    _init("progress_logs",[])
    with st.form("pg"):
        c1,c2,c3 = st.columns(3)
        d  = c1.date_input("Ngày", datetime.date.today())
        w  = c2.number_input("Cân nặng (kg)",30.0,200.0,float(p.get("weight",70)),0.1)
        s  = c3.number_input("Buổi tập",0,5,0)
        nt = st.text_input("Ghi chú",placeholder="Cảm nhận hôm nay…")
        ok = st.form_submit_button("✅ Lưu log", use_container_width=True)
    if ok:
        entry = {"date":str(d),"weight":w,"workouts":s,"note":clean_text(nt)}
        logs  = st.session_state.progress_logs
        idx   = next((i for i,l in enumerate(logs) if l["date"]==str(d)),None)
        if idx is not None: logs[idx] = entry
        else: logs.append(entry)
        logs.sort(key=lambda x:x["date"])
        st.session_state.progress_logs = logs
        st.success(f"✅ Đã lưu {d}!"); st.rerun()

    logs = st.session_state.progress_logs
    if not logs:
        st.markdown(f"<div style='text-align:center;color:{C['muted']};padding:20px 0;font-size:.85rem'>Chưa có dữ liệu. Hãy lưu log đầu tiên!</div>",unsafe_allow_html=True)
        return

    ws  = [l["weight"] for l in logs]
    ds  = [l["date"]   for l in logs]
    d0  = ws[0]; dc = ws[-1]; dlt = round(dc-d0,1)
    ts  = sum(l["workouts"] for l in logs)
    c1,c2,c3 = st.columns(3)
    c1.metric("Cân hiện tại", f"{dc} kg", f"{dlt:+.1f} kg")
    c2.metric("Tổng buổi tập", str(ts))
    c3.metric("Ngày ghi log",  str(len(logs)))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ds,y=ws,mode="lines+markers",
        line=dict(color="#8b5cf6",width=2),marker=dict(size=6,color="#a78bfa"),
        fill="tozeroy",fillcolor="rgba(139,92,246,0.07)",
        hovertemplate="<b>%{x}</b><br>%{y} kg<extra></extra>"))
    fig.update_layout(margin=dict(l=0,r=0,t=4,b=0),height=145,
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False,color="#707070",tickfont=dict(size=9)),
        yaxis=dict(showgrid=True,gridcolor="#1c1c1c",color="#707070",tickfont=dict(size=9)),
        showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    for l in reversed(logs[-5:]):
        dv = round(l["weight"]-d0,1)
        cl = C["success"] if dv<=0 else C["warning"]
        st.markdown(
            f"<div style='display:flex;gap:8px;font-size:.76rem;padding:5px 0;border-bottom:1px solid {C['border']}'>"
            f"<span style='color:{C['muted']};min-width:72px'>{l['date']}</span>"
            f"<span style='font-weight:700;color:{C['text']};min-width:52px'>{l['weight']} kg</span>"
            f"<span style='color:{cl};min-width:46px'>{dv:+.1f}</span>"
            f"<span style='color:{C['muted']};flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap'>{l['note'] or '—'}</span>"
            f"</div>", unsafe_allow_html=True)
    if st.button("🗑️ Xoá tất cả", key="del_pg"): st.session_state.progress_logs=[]; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — ĐÁNH GIÁ AI
# ══════════════════════════════════════════════════════════════════════════════
def _tab_eval():
    _sec("Đánh giá AI")
    _init("eval_logs",[])
    col1,col2 = st.columns([3,1])
    with col1:
        if st.button("🚀 Chạy toàn bộ", use_container_width=True, key="run_eval"):
            with st.spinner(f"Đang test {len(EVAL_DATA)} câu…"):
                from modules.chat import chat_response
                logs=[]
                for item in EVAL_DATA:
                    try: ans = chat_response([],item["question"])
                    except Exception as e: ans=f"ERROR:{e}"
                    logs.append(evaluate_item(item,ans))
                st.session_state.eval_logs=logs
            st.rerun()
    with col2:
        if st.button("🔄",use_container_width=True,key="rst_eval"):
            st.session_state.eval_logs=[]; st.rerun()

    logs = st.session_state.eval_logs
    if not logs:
        st.markdown(f"<p style='font-size:.78rem;color:{C['muted']};margin:8px 0'>Hoặc test từng câu:</p>",unsafe_allow_html=True)
        cat_c={"Lịch tập":"#8b5cf6","Dinh dưỡng":"#06b6d4","Dụng cụ":"#22c55e","Phục hồi":"#f59e0b"}
        for i,item in enumerate(EVAL_DATA):
            ca,cb = st.columns([5,1])
            with ca:
                cc=cat_c.get(item["category"],"#6b7280")
                st.markdown(f"<div style='font-size:.77rem;color:{C['text_sub']};padding:3px 0'>"
                            f"<span style='color:{cc};font-weight:700'>[{item['category']}]</span> {item['question']}</div>",
                            unsafe_allow_html=True)
            with cb:
                if st.button("▶",key=f"ev{i}",use_container_width=True):
                    with st.spinner("…"):
                        from modules.chat import chat_response
                        try: ans=chat_response([],item["question"])
                        except Exception as e: ans=f"ERROR:{e}"
                    entry=evaluate_item(item,ans)
                    ex=next((j for j,l in enumerate(st.session_state.eval_logs) if l["question"]==item["question"]),None)
                    if ex is not None: st.session_state.eval_logs[ex]=entry
                    else: st.session_state.eval_logs.append(entry)
                    st.rerun()
        return

    df=build_eval_dataframe(logs); m=compute_metrics(df); acc=m["accuracy"] or 0
    c1,c2,c3=st.columns(3)
    c1.metric("Accuracy",f"{acc:.1%}"); c2.metric("Đã test",f"{m['total']}/{len(EVAL_DATA)}"); c3.metric("Đúng",f"{m['correct']}/{m['total']}")
    if m["total"]==len(EVAL_DATA): (st.success("✅ Đạt ≥ 80%") if acc>=.8 else st.warning("⚠️ < 80%"))
    by_cat=df.groupby("category")["correct_num"].mean().round(4).to_dict()
    fig=go.Figure(go.Bar(x=list(by_cat.values()),y=list(by_cat.keys()),orientation="h",
        marker_color=["#8b5cf6" if v>=.8 else "#ef4444" for v in by_cat.values()],
        text=[f"{v:.0%}" for v in by_cat.values()],textposition="outside"))
    fig.update_layout(xaxis=dict(range=[0,1.3],tickformat=".0%",color="#707070",tickfont=dict(size=9)),
        yaxis=dict(color="#707070",tickfont=dict(size=9)),margin=dict(l=0,r=24,t=4,b=0),height=155,
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#c0c0c0"))
    st.plotly_chart(fig,use_container_width=True)
    for l in logs:
        ok=l["correct"]
        st.markdown(f"<div style='font-size:.76rem;padding:4px 0;border-bottom:1px solid {C['border']}'>"
                    f"<span style='color:{'#22c55e' if ok else '#ef4444'}'>{'✅' if ok else '❌'}</span>"
                    f" <span style='color:{C['text_sub']}'>{l['question'][:54]}{'…' if len(l['question'])>54 else ''}</span></div>",
                    unsafe_allow_html=True)
    st.download_button("📥 Tải CSV",data=df.to_csv(index=False).encode("utf-8-sig"),
                       file_name="eval.csv",mime="text/csv",use_container_width=True,key="dl_ev")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — NHẬN DIỆN ẢNH
# ══════════════════════════════════════════════════════════════════════════════
def _tab_image():
    _sec("Nhận diện ảnh")
    _init("sb_pred",None); _init("sb_result","")
    mode     = st.radio("Loại ảnh",["🏋️ Dụng cụ","🍽️ Món ăn"],horizontal=True)
    uploaded = st.file_uploader("Chọn ảnh (JPG/PNG/WEBP)",type=["jpg","jpeg","png","webp"],key="sb_up")
    note     = st.text_input("Ghi chú",placeholder="VD: tôi bị đau lưng…",key="sb_nt")
    if not uploaded: return
    img=Image.open(uploaded)
    st.image(img,use_container_width=True)
    if st.button("🔍 Phân tích",use_container_width=True,key="sb_an"):
        with st.spinner("Đang phân tích…"):
            try:
                if "Dụng cụ" in mode:
                    pred,detail=analyze_equipment_image(img,note)
                    st.session_state.sb_pred=pred; st.session_state.sb_result=detail
                else:
                    st.session_state.sb_pred=None; st.session_state.sb_result=analyze_food_image(img)
            except Exception as e:
                st.session_state.sb_pred=None; st.session_state.sb_result=f"❌ {e}"
    pred=st.session_state.sb_pred
    if pred and not pred.get("fallback"):
        lm={"benchPress":"Ghế tập ngực","dumbBell":"Tạ đơn","kettleBell":"Tạ ấm","pullBar":"Xà đơn","treadMill":"Máy chạy bộ"}
        cls=pred["class_name"]; cf=pred["confidence"]
        st.markdown(f"<div style='background:#1f1b33;border:1px solid #7c3aed55;border-radius:10px;padding:10px;text-align:center;margin:8px 0'>"
                    f"<div style='font-size:.64rem;color:#7a7298'>Phát hiện</div>"
                    f"<div style='font-size:1rem;font-weight:800;color:#a78bfa'>{lm.get(cls,cls)}</div>"
                    f"<div style='font-weight:700;color:{'#4ade80' if cf>=.7 else '#fbbf24'}'>{cf:.1%}</div></div>",
                    unsafe_allow_html=True)
        for c,prob in sorted(pred["all_probs"].items(),key=lambda x:-x[1])[:5]:
            it=c==cls
            st.markdown(f"<div style='display:flex;align-items:center;gap:5px;margin-bottom:3px'>"
                        f"<div style='width:86px;font-size:.72rem;color:{'#a78bfa' if it else '#7a7298'};font-weight:{'700' if it else '400'}'>{lm.get(c,c)}</div>"
                        f"<div style='flex:1;background:#0d0b14;border-radius:3px;height:5px'><div style='width:{prob*100:.1f}%;height:100%;background:{'#7c3aed' if it else '#332d55'};border-radius:3px'></div></div>"
                        f"<div style='width:30px;font-size:.72rem;color:{'#a78bfa' if it else '#7a7298'}'>{prob:.0%}</div></div>",
                        unsafe_allow_html=True)
    if st.session_state.sb_result:
        st.divider(); st.markdown(st.session_state.sb_result)
        st.download_button("📥 Tải kết quả",data=st.session_state.sb_result,
                           file_name="phantich.md",mime="text/markdown",
                           use_container_width=True,key="dl_img")

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def render_sidebar() -> dict:
    with st.sidebar:
        # Logo
        b64=_logo()
        lh=(f'<img src="data:image/png;base64,{b64}" style="width:30px;height:30px;object-fit:contain;border-radius:6px;margin-right:8px">'
            if b64 else '<span style="font-size:1.4rem;margin-right:8px">💪</span>')
        st.markdown(f"""
        <div style="padding:12px 0 8px;display:flex;align-items:center">
          {lh}
          <div>
            <div style="font-size:1.05rem;font-weight:800;
              background:linear-gradient(135deg,#a78bfa,#7c3aed);
              -webkit-background-clip:text;-webkit-text-fill-color:transparent">GymPro AI</div>
            <div style="font-size:.58rem;color:#7a7298;letter-spacing:.08em;text-transform:uppercase">Personal Fitness Coach</div>
          </div>
        </div>""", unsafe_allow_html=True)

        # Chỉ số nhanh
        pr=st.session_state.get("saved_profile",{})
        if pr:
            bmi=format_bmi(pr["weight"],pr["height"])
            td =calc_tdee(pr["weight"],pr["height"],pr["age"],pr["gender"],pr["activity"])
            st.markdown(f"""
            <div style="background:#1a1630;border:1px solid #4e468077;border-radius:9px;padding:9px 11px;margin-bottom:8px">
              <div style="font-size:.62rem;text-transform:uppercase;letter-spacing:.07em;color:#a78bfa;font-weight:700;margin-bottom:7px">👤 {pr.get('name','User')}</div>
              <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:4px">
                <div style="background:#0d0b14;border-radius:5px;padding:5px;text-align:center"><div style="font-size:.56rem;color:#7a7298">BMI</div><div style="font-size:.88rem;font-weight:700;color:{bmi['color']}">{bmi['bmi']}</div></div>
                <div style="background:#0d0b14;border-radius:5px;padding:5px;text-align:center"><div style="font-size:.56rem;color:#7a7298">TDEE</div><div style="font-size:.88rem;font-weight:700;color:#a78bfa">{td['tdee']}</div></div>
                <div style="background:#0d0b14;border-radius:5px;padding:5px;text-align:center"><div style="font-size:.56rem;color:#7a7298">Cut</div><div style="font-size:.88rem;font-weight:700;color:#4ade80">{td['cut']}</div></div>
                <div style="background:#0d0b14;border-radius:5px;padding:5px;text-align:center"><div style="font-size:.56rem;color:#7a7298">Bulk</div><div style="font-size:.88rem;font-weight:700;color:#fbbf24">{td['bulk']}</div></div>
              </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background:#1a1630;border:1px solid #332d55;border-radius:8px;padding:9px;text-align:center;color:#7a7298;font-size:.8rem;margin-bottom:8px'>Chưa có hồ sơ — điền tab 👤</div>",unsafe_allow_html=True)

        # 6 TABS
        p = st.session_state.get("saved_profile", _DP)
        t1,t2,t3,t4,t5,t6 = st.tabs(["👤","🗓️","🥗","📈","📊","📸"])
        with t1: _tab_profile()
        with t2: _tab_workout(p)
        with t3: _tab_meal(p)
        with t4: _tab_progress(p)
        with t5: _tab_eval()
        with t6: _tab_image()

        st.markdown("<p style='color:#4e4680;font-size:.62rem;text-align:center;margin-top:12px'>GymPro AI v1.0.0 · Groq LLaMA</p>",unsafe_allow_html=True)

    p = st.session_state.get("saved_profile", _DP)
    return {
        "name":    p.get("name","User"),
        "age":     p.get("age",25),
        "gender":  p.get("gender","Nam / Male"),
        "weight":  p.get("weight",70.0),
        "height":  p.get("height",170.0),
        "activity":p.get("activity","Vừa (3-5 ngày/tuần) / Moderate"),
        "level":   p.get("level",list(FITNESS_LEVELS.keys())[0]),
        "goal":    p.get("goal",FITNESS_GOALS[0]),
        "diet":    p.get("diet",DIET_TYPES[0]),
        "tdee":    calc_tdee(p.get("weight",70),p.get("height",170),
                             p.get("age",25),p.get("gender","Nam / Male"),
                             p.get("activity","Vừa (3-5 ngày/tuần) / Moderate")),
        "bmi":     format_bmi(p.get("weight",70),p.get("height",170)),
    }