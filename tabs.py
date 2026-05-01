"""
ui/tabs.py  —  CHỈ chứa render_chat_tab()
Mọi chức năng khác đã chuyển sang ui/sidebar.py
"""

import datetime
import streamlit as st

from modules.chat import chat_response
from modules.preprocessing import transform_profile, profile_to_prompt_context, clean_text

C = {
    "bg2":       "#0a0a0a",
    "bg3":       "#111111",
    "border":    "#2a2a2a",
    "border2":   "#3a3a3a",
    "text":      "#f0f0f0",
    "text_sub":  "#c0c0c0",
    "muted":     "#707070",
    "accent":    "#8b5cf6",
    "accent_l":  "#a78bfa",
    "accent_d":  "#6d28d9",
    "accent_dim":"#8b5cf620",
    "success":   "#22c55e",
}


def _init(key, val):
    if key not in st.session_state:
        st.session_state[key] = val


def _bubble(role: str, content: str):
    t = datetime.datetime.now().strftime("%H:%M")
    if role == "user":
        st.markdown(f"""
        <div style="display:flex;justify-content:flex-end;margin:10px 0">
          <div style="max-width:76%">
            <div style="background:linear-gradient(135deg,{C['accent_d']},{C['accent']});
                color:#fff;border-radius:18px 18px 4px 18px;
                padding:12px 16px;font-size:.9rem;line-height:1.65;
                box-shadow:0 4px 20px {C['accent_dim']}">{content}</div>
            <div style="text-align:right;font-size:.67rem;color:{C['muted']};
                margin-top:4px;padding-right:4px">🧑 Bạn · {t}</div>
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="display:flex;justify-content:flex-start;margin:10px 0">
          <div style="max-width:80%">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
              <div style="width:28px;height:28px;border-radius:50%;
                  background:linear-gradient(135deg,{C['accent']},{C['accent_d']});
                  display:flex;align-items:center;justify-content:center;
                  font-size:.85rem;flex-shrink:0">💪</div>
              <span style="font-size:.74rem;font-weight:700;color:{C['accent_l']}">GymPro AI</span>
              <span style="font-size:.67rem;color:{C['muted']}">{t}</span>
            </div>
            <div style="background:{C['bg3']};border:1px solid {C['border']};
                color:{C['text']};border-radius:4px 18px 18px 18px;
                padding:14px 16px;font-size:.9rem;line-height:1.72">{content}</div>
          </div>
        </div>""", unsafe_allow_html=True)


def render_chat_tab(profile: dict):
    _init("chat_messages", [])

    # Status bar
    n = len(st.session_state.chat_messages) // 2
    st.markdown(f"""
    <div style="background:{C['bg2']};border:1px solid {C['border']};
        border-radius:14px;padding:11px 18px;margin-bottom:18px;
        display:flex;align-items:center;gap:12px">
      <div style="width:34px;height:34px;border-radius:50%;
          background:linear-gradient(135deg,{C['accent']},{C['accent_d']});
          display:flex;align-items:center;justify-content:center;
          font-size:.95rem;flex-shrink:0">💪</div>
      <div>
        <div style="font-weight:700;font-size:.9rem;color:{C['text']}">GymPro AI</div>
        <div style="font-size:.7rem;color:{C['success']};display:flex;align-items:center;gap:5px">
          <span style="width:6px;height:6px;border-radius:50%;
              background:{C['success']};display:inline-block"></span>
          Trực tuyến · Sẵn sàng tư vấn
        </div>
      </div>
      <div style="margin-left:auto;font-size:.74rem;color:{C['muted']}">
        {"Chưa có tin nhắn" if n == 0 else f"{n} tin nhắn"}
      </div>
    </div>""", unsafe_allow_html=True)

    # ── Welcome (chỉ hiện khi chưa có chat, KHÔNG có quick prompt buttons) ────
    if not st.session_state.chat_messages:
        st.markdown(f"""
        <div style="display:flex;flex-direction:column;align-items:center;
            justify-content:center;padding:60px 20px 40px;text-align:center">
          <div style="width:76px;height:76px;border-radius:50%;
              background:linear-gradient(135deg,{C['accent']},{C['accent_d']});
              display:flex;align-items:center;justify-content:center;
              font-size:2.1rem;margin-bottom:20px;
              box-shadow:0 8px 32px {C['accent_dim']}">💪</div>
          <div style="font-size:1.3rem;font-weight:800;color:{C['text']};margin-bottom:8px">
            Xin chào, {profile['name']}!</div>
          <div style="font-size:.9rem;color:{C['muted']};max-width:420px;
              line-height:1.75;margin-bottom:24px">
            Tôi là <b style="color:{C['accent_l']}">GymPro AI</b> —
            huấn luyện viên cá nhân của bạn.<br>
            Hãy đặt câu hỏi về tập luyện, dinh dưỡng hoặc sức khoẻ.
          </div>
          <div style="font-size:.78rem;color:{C['muted']};
              background:{C['bg3']};border:1px solid {C['border2']};
              border-radius:10px;padding:10px 18px">
            💡 Lịch tập · Thực đơn · Tiến độ · Đánh giá · Ảnh
            — tất cả nằm ở <b style="color:{C['accent_l']}">sidebar bên trái</b>
          </div>
        </div>""", unsafe_allow_html=True)

    # ── Lịch sử hội thoại ─────────────────────────────────────────────────────
    for msg in st.session_state.chat_messages:
        _bubble(msg["role"], msg["content"])

    st.markdown("<div style='height:100px'></div>", unsafe_allow_html=True)

    # ── Chat input ────────────────────────────────────────────────────────────
    user_input = st.chat_input("Nhập câu hỏi về tập luyện, dinh dưỡng…")
    if user_input and user_input.strip():
        _send(clean_text(user_input.strip()), profile)
        st.rerun()

    # ── Nút xoá ───────────────────────────────────────────────────────────────
    if st.session_state.chat_messages:
        _, col = st.columns([8, 1])
        with col:
            if st.button("🗑️", key="clr_chat", use_container_width=True):
                st.session_state.chat_messages = []
                st.rerun()


def _send(text: str, profile: dict):
    st.session_state.chat_messages.append({"role": "user", "content": text})
    with st.spinner("GymPro đang suy nghĩ…"):
        try:
            if len(st.session_state.chat_messages) == 1:
                ctx = profile_to_prompt_context(
                    transform_profile(
                        profile["weight"], profile["height"], profile["age"],
                        profile["gender"], profile["goal"], profile["level"],
                    )
                ) + "\n\n" + text
            else:
                ctx = text
            ans = chat_response(st.session_state.chat_messages[:-1], ctx)
        except Exception as e:
            ans = f"❌ Lỗi kết nối: {e}"
    st.session_state.chat_messages.append({"role": "assistant", "content": ans})