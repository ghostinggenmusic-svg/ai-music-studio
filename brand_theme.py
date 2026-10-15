"""Ghosting Music visual theme; image remains transparent PNG."""
from pathlib import Path
import base64
import streamlit as st


def apply_brand_theme():
    path=Path(__file__).with_name('ghosting_music_logo.png')
    logo=base64.b64encode(path.read_bytes()).decode() if path.exists() else ''
    background=f'url("data:image/png;base64,{logo}")' if logo else 'none'
    css='''
    <style>
    :root { color-scheme: dark; }
    [data-testid="stAppViewContainer"] {
      color:#eef3ff;
      background:radial-gradient(ellipse at 7% 6%,#243866 0,transparent 40%),radial-gradient(ellipse at 95% 22%,#392059 0,transparent 46%),radial-gradient(ellipse at 55% 100%,#123e45 0,transparent 48%),#080e1e;
    }
    [data-testid="stMain"] {position:relative; isolation:isolate;}
    [data-testid="stMain"]::before {content:"";position:fixed;inset:60px 0 0;pointer-events:none;z-index:-1;background-image:LOGO_BACKGROUND;background-position:78% 48%;background-repeat:no-repeat;background-size:min(65vw,820px);opacity:.12;}
    [data-testid="stMainBlockContainer"] {padding-top:2rem;max-width:1500px;}
    [data-testid="stHeader"] {background:rgba(8,14,30,.88);backdrop-filter:blur(18px);}
    [data-testid="stSidebar"] {background:linear-gradient(165deg,#111c35,#171329 65%,#0b2630);border-right:1px solid #6379c340;color:#edf3ff;}
    [data-testid="stAppViewContainer"] h1,[data-testid="stAppViewContainer"] h2,[data-testid="stAppViewContainer"] h3,[data-testid="stAppViewContainer"] h4 {color:#f1f4ff;letter-spacing:-.025em;}
    [data-testid="stAppViewContainer"] p,[data-testid="stAppViewContainer"] label,[data-testid="stAppViewContainer"] [data-testid="stWidgetLabel"] {color:#e6ecff;}
    [data-testid="stCaptionContainer"] p {color:#b3c0de!important;}
    [data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea {background:#101b30!important;color:#f4f7ff!important;caret-color:#62e4e5;}
    [data-testid="stTextInput"]>div,[data-testid="stTextArea"]>div {border-color:#566a9566;border-radius:12px;}
    [data-baseweb="select"]>div {background:#14223b;color:#f4f7ff;border-color:#566a9588;border-radius:12px;}
    [role="listbox"] {background:#15223a;color:#f4f7ff;}
    [role="option"] {color:#f4f7ff;}
    [data-testid="stChatInput"] {background:#101c33;border:1px solid #8396d466;border-radius:16px;}
    [data-testid="stChatInput"] textarea {color:#f4f7ff;background:transparent;}
    [data-testid="stChatMessage"] {background:linear-gradient(135deg,#182842e8,#211b3be8);border:1px solid #738bd833;border-radius:18px;box-shadow:0 8px 32px #0002;}
    [data-testid="stCode"] pre {background:#0c1629!important;color:#e5efff!important;border:1px solid #586da64d;border-radius:12px;}
    [data-testid="stExpander"] {background:#121f35b8;border:1px solid #657db744;border-radius:15px;}
    [data-testid="stExpander"] summary {color:#e6ecff;}
    [data-testid="stButton"] button,[data-testid="stLinkButton"] a {background:#22334f;border:1px solid #7c94cd55;color:#edf4ff;border-radius:12px;transition:background .2s,transform .2s;}
    [data-testid="stButton"] button:hover,[data-testid="stLinkButton"] a:hover {background:#35466a;border-color:#73d6e9;}
    [data-testid="stButton"] button[kind="primary"] {background:linear-gradient(110deg,#7c3ee8,#b53ac0 55%,#e76b50);border:0;color:white;box-shadow:0 6px 24px #b43db733;}
    [data-testid="stMetric"] {padding:16px;border:1px solid #5bcbd944;border-radius:14px;background:linear-gradient(120deg,#103749cc,#242346bb);}
    [data-testid="stMetricValue"] {color:#7ee9db;}
    a {color:#80dfff;}
    hr {border-color:#788eb633;}
    .gm-brand {display:flex;align-items:center;gap:18px;padding:14px 22px;margin:0 0 26px;border:1px solid #8298da44;border-radius:22px;background:linear-gradient(110deg,#142945d9,#292044b3);box-shadow:0 16px 45px #0003;}
    .gm-brand img {width:108px;height:108px;object-fit:contain;filter:drop-shadow(0 0 16px #7b53d84d);}
    .gm-brand .gm-kicker {color:#72e4dd;font:600 11px/1.6 sans-serif;letter-spacing:.23em;}
    .gm-brand .gm-name {font:800 clamp(22px,3vw,36px)/1.15 sans-serif;letter-spacing:.025em;color:#fff;}
    .gm-brand .gm-sub {color:#bac7df;font-size:13px;margin-top:8px;}
    @media(max-width:640px){.gm-brand{gap:10px;padding:12px;}.gm-brand img{width:76px;height:76px;}[data-testid="stMain"]::before{background-size:95vw;background-position:50% 25%;opacity:.09;}}
    </style>
    '''.replace('LOGO_BACKGROUND',background)
    st.markdown(css,unsafe_allow_html=True)
    image=f'<img src="data:image/png;base64,{logo}" alt="Ghosting Music logo">' if logo else ''
    st.markdown('<div class="gm-brand">'+image+'<div><div class="gm-kicker">CREATE • PRODUCE • RELEASE</div><div class="gm-name">GHOSTING MUSIC</div><div class="gm-sub">Music Studio · โปรดิวเซอร์สมพงษ์</div></div></div>',unsafe_allow_html=True)
