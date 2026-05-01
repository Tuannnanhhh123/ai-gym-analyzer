import streamlit as st
import base64, os
from config import APP_TITLE, GROQ_API_KEY
from ui.sidebar import render_sidebar
from ui.tabs import render_chat_tab

st.set_page_config(
    page_title="GymPro AI",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
)

def _load_logo(path="assets/logo.png") -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

LOGO_B64  = _load_logo()
LOGO_HTML = (
    f'<img src="data:image/png;base64,{LOGO_B64}" '
    f'style="width:46px;height:46px;object-fit:contain;border-radius:10px">'
    if LOGO_B64 else '<span style="font-size:2.2rem">💪</span>'
)

T = {
    "bg":         "#000000", "bg2":        "#0a0a0a",
    "bg3":        "#111111", "bg4":        "#161616",
    "bg5":        "#1c1c1c", "bg6":        "#222222",
    "border":     "#2a2a2a", "border2":    "#3a3a3a", "border3": "#4a4a4a",
    "text":       "#f0f0f0", "text_sub":   "#c0c0c0", "text_muted": "#707070",
    "accent":     "#8b5cf6", "accent_l":   "#a78bfa",
    "accent_d":   "#6d28d9", "accent_dim": "#8b5cf620", "glow": "#8b5cf640",
    "success":    "#22c55e", "warning":    "#f59e0b",  "danger": "#ef4444",
}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
*,*::before,*::after{{box-sizing:border-box}}
html,body,[class*="css"]{{font-family:'Inter',sans-serif;-webkit-font-smoothing:antialiased}}

.stApp{{background:{T['bg']} !important}}
.stApp,.stApp p,.stApp span,.stApp div,
.stApp li,.stApp td,.stApp th{{color:{T['text']} !important}}
.stApp h1,.stApp h2,.stApp h3,.stApp h4{{color:{T['accent_l']} !important;font-weight:700 !important}}

section[data-testid="stSidebar"]{{background:{T['bg3']} !important;border-right:1px solid {T['border']} !important}}
section[data-testid="stSidebar"] *{{color:{T['text']} !important}}
section[data-testid="stSidebar"] label{{color:{T['text_muted']} !important;font-weight:600 !important;font-size:.72rem !important;text-transform:uppercase;letter-spacing:.07em}}

/* Sidebar tabs */
section[data-testid="stSidebar"] .stTabs [data-baseweb="tab-list"]{{background:{T['bg4']} !important;border-radius:10px !important;padding:3px !important;border:1px solid {T['border']} !important;gap:2px !important}}
section[data-testid="stSidebar"] .stTabs [data-baseweb="tab"]{{border-radius:7px !important;padding:8px 4px !important;font-size:.95rem !important;color:{T['text_muted']} !important;background:transparent !important;transition:all .2s !important;flex:1 !important;text-align:center !important}}
section[data-testid="stSidebar"] .stTabs [aria-selected="true"]{{background:{T['accent']} !important;color:#fff !important;box-shadow:0 2px 10px {T['glow']} !important}}

label,.stSelectbox label,.stNumberInput label,.stTextInput label,
.stTextArea label,.stSlider label,.stRadio label,.stMultiSelect label{{
    color:{T['text_muted']} !important;font-weight:600 !important;
    font-size:.72rem !important;text-transform:uppercase;letter-spacing:.06em}}

.stTextInput>div>div>input,.stNumberInput>div>div>input,.stTextArea>div>textarea{{
    background:{T['bg4']} !important;color:{T['text']} !important;
    border:1.5px solid {T['border2']} !important;border-radius:8px !important;
    font-size:.9rem !important;caret-color:{T['accent']} !important}}
.stTextInput>div>div>input::placeholder,.stTextArea>div>textarea::placeholder{{color:{T['text_muted']} !important;opacity:1 !important}}
.stTextInput>div>div>input:focus,.stNumberInput>div>div>input:focus,.stTextArea>div>textarea:focus{{
    border-color:{T['accent']} !important;box-shadow:0 0 0 3px {T['glow']} !important;outline:none !important}}

.stSelectbox>div>div{{background:{T['bg4']} !important;color:{T['text']} !important;border:1.5px solid {T['border2']} !important;border-radius:8px !important}}
[data-baseweb="popover"] ul,[data-baseweb="menu"]{{background:{T['bg5']} !important;border:1px solid {T['border2']} !important;border-radius:10px !important}}
[data-baseweb="menu"] li{{background:{T['bg5']} !important;color:{T['text']} !important;font-size:.88rem !important}}
[data-baseweb="menu"] li:hover{{background:{T['bg6']} !important}}

.stButton>button{{border-radius:8px !important;font-weight:600 !important;border:1.5px solid {T['border2']} !important;background:{T['bg4']} !important;color:{T['text_sub']} !important;font-size:.85rem !important;transition:all .18s !important;padding:8px 16px !important}}
.stButton>button:hover{{border-color:{T['accent']} !important;color:{T['accent_l']} !important;background:{T['bg5']} !important;box-shadow:0 0 16px {T['accent_dim']} !important}}
.stFormSubmitButton>button{{background:{T['accent']} !important;color:#fff !important;border:none !important;font-weight:700 !important;border-radius:8px !important;box-shadow:0 4px 20px {T['glow']} !important;transition:all .2s !important}}
.stFormSubmitButton>button:hover{{background:{T['accent_d']} !important;transform:translateY(-1px) !important}}
.stDownloadButton>button{{background:transparent !important;border:1.5px solid {T['accent']} !important;color:{T['accent_l']} !important;font-weight:600 !important;border-radius:8px !important;transition:all .2s !important}}
.stDownloadButton>button:hover{{background:{T['accent_dim']} !important}}

[data-testid="stChatInput"]{{
    position:fixed !important;bottom:20px !important;
    left:calc(50% + 155px) !important;transform:translateX(-50%) !important;
    width:min(700px,56vw) !important;z-index:9999 !important;
    background:{T['bg3']} !important;border:1.5px solid {T['border2']} !important;
    border-radius:16px !important;padding:6px 10px !important;
    box-shadow:0 0 0 1px {T['border']},0 8px 40px rgba(0,0,0,.8),0 0 30px {T['accent_dim']} !important}}
[data-testid="stChatInput"] textarea{{background:transparent !important;color:{T['text']} !important;border:none !important;font-size:.93rem !important;caret-color:{T['accent']} !important;line-height:1.6 !important}}
[data-testid="stChatInput"] textarea::placeholder{{color:{T['text_muted']} !important;opacity:1 !important}}
[data-testid="stChatInput"] button{{background:{T['accent']} !important;border-radius:10px !important;border:none !important;color:white !important;width:36px !important;height:36px !important;box-shadow:0 2px 12px {T['glow']} !important;transition:all .18s !important}}
[data-testid="stChatInput"] button:hover{{background:{T['accent_d']} !important;transform:scale(1.05) !important}}

[data-testid="stChatMessage"]{{background:transparent !important;border:none !important;border-radius:0 !important;padding:4px 0 !important;margin:0 !important}}

[data-testid="metric-container"]{{background:{T['bg2']} !important;border-radius:12px !important;padding:14px 16px !important;border:1px solid {T['border']} !important;transition:border-color .2s !important}}
[data-testid="metric-container"]:hover{{border-color:{T['border3']} !important}}
[data-testid="stMetricValue"]{{color:{T['accent_l']} !important;font-weight:800 !important;font-size:1.4rem !important}}
[data-testid="stMetricLabel"]{{color:{T['text_muted']} !important;font-weight:600 !important;font-size:.72rem !important;text-transform:uppercase;letter-spacing:.06em}}

[data-testid="stForm"]{{background:{T['bg2']} !important;border-radius:16px !important;padding:20px !important;border:1px solid {T['border']} !important}}
[data-testid="stFileUploader"]{{background:{T['bg4']} !important;border:2px dashed {T['border2']} !important;border-radius:12px !important;transition:border-color .2s !important}}
[data-testid="stFileUploader"]:hover{{border-color:{T['accent']} !important}}
.stMultiSelect [data-baseweb="tag"]{{background:{T['accent_dim']} !important;color:{T['accent_l']} !important;border-radius:6px !important;font-weight:500 !important;border:1px solid {T['accent']}44 !important}}
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"]{{background:{T['accent']} !important;border:2px solid {T['accent_l']} !important}}
.stProgress>div>div>div{{background:linear-gradient(90deg,{T['accent_d']},{T['accent_l']}) !important;border-radius:4px !important}}

::-webkit-scrollbar{{width:4px;height:4px}}
::-webkit-scrollbar-track{{background:transparent}}
::-webkit-scrollbar-thumb{{background:{T['border2']};border-radius:2px}}
::-webkit-scrollbar-thumb:hover{{background:{T['accent']}}}
hr{{border-color:{T['border']} !important;opacity:.6 !important}}
.stAlert{{border-radius:10px !important;border-left-width:4px !important}}
section.main .block-container{{padding-bottom:120px !important}}
.stSpinner>div{{border-top-color:{T['accent']} !important}}
.stApp small,.stCaption{{color:{T['text_muted']} !important;font-size:.76rem !important}}
[data-testid="stDataFrame"]{{border:1px solid {T['border']} !important;border-radius:10px !important}}
.stRadio [data-testid="stMarkdownContainer"] p{{color:{T['text_sub']} !important}}
</style>
""", unsafe_allow_html=True)

if not GROQ_API_KEY:
    st.error(
        "⚠️ **GROQ_API_KEY chưa cấu hình!**\n\n"
        "Tạo file `.env`:\n```\nGROQ_API_KEY=your_key\n```\n\n"
        "Lấy key miễn phí: https://console.groq.com/keys"
    )
    st.stop()

profile = render_sidebar()

st.markdown(f"""
<div style="background:linear-gradient(135deg,#111111,#0a0a0a);
    border:1px solid #2a2a2a;border-radius:16px;padding:18px 24px;
    margin-bottom:16px;display:flex;align-items:center;gap:16px;
    position:relative;overflow:hidden">
  <div style="position:absolute;top:-40px;right:-40px;width:180px;height:180px;
    background:radial-gradient(circle,{T['glow']},transparent 70%);pointer-events:none"></div>
  {LOGO_HTML}
  <div style="flex:1">
    <div style="font-size:1.5rem;font-weight:900;letter-spacing:-.02em;
        background:linear-gradient(135deg,#ffffff,{T['accent_l']});
        -webkit-background-clip:text;-webkit-text-fill-color:transparent">GymPro AI</div>
    <div style="color:{T['text_muted']};font-size:.8rem;margin-top:2px">
        Xin chào, <b style="color:{T['accent_l']}">{profile['name']}</b> 👋
        &nbsp;·&nbsp; Huấn luyện viên cá nhân · Dinh dưỡng · Nhận diện dụng cụ
    </div>
  </div>
  <div style="display:flex;gap:8px;flex-shrink:0">
    <div style="background:{T['bg4']};border:1px solid {T['border2']};
        border-radius:8px;padding:6px 14px;text-align:center">
      <div style="font-size:.58rem;color:{T['text_muted']};text-transform:uppercase;letter-spacing:.06em">BMI</div>
      <div style="font-size:1rem;font-weight:800;color:{profile['bmi']['color']}">{profile['bmi']['bmi']}</div>
    </div>
    <div style="background:{T['bg4']};border:1px solid {T['border2']};
        border-radius:8px;padding:6px 14px;text-align:center">
      <div style="font-size:.58rem;color:{T['text_muted']};text-transform:uppercase;letter-spacing:.06em">TDEE</div>
      <div style="font-size:1rem;font-weight:800;color:{T['accent_l']}">{profile['tdee']['tdee']}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# TRANG CHÍNH = CHỈ CHAT. Không tabs, không gì khác.
# ═══════════════════════════════════════════════════
render_chat_tab(profile)