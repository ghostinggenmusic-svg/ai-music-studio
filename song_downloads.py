"""Download completed source audio once, with a manual browser fallback."""
import base64
import hashlib
import json
import requests
import streamlit as st
import streamlit.components.v1 as components

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_audio(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.content
    if not data or len(data) > 80_000_000:
        raise ValueError("Invalid audio size")
    mime = response.headers.get("Content-Type", "audio/mpeg").split(";")[0]
    wav = data[:4] == b"RIFF" and data[8:12] == b"WAVE"
    return data, "audio/wav" if wav else mime, "wav" if wav else "mp3"

def render_download(url, index, automatic):
    token = hashlib.sha256(url.encode()).hexdigest()
    try:
        data, mime, extension = fetch_audio(url)
    except (requests.RequestException, ValueError):
        st.warning("เตรียมไฟล์ดาวน์โหลดไม่สำเร็จ ใช้ลิงก์เปิดไฟล์เพลงเพื่อลองใหม่")
        return
    filename = f"Ghosting-Music-track-{index + 1}.{extension}"
    st.download_button("⬇️ ดาวน์โหลดเพลง " + str(index + 1), data,
                       file_name=filename, mime=mime, key="download_" + token)
    sent = st.session_state.setdefault("auto_download_sent", set())
    if automatic and token not in sent:
        encoded = base64.b64encode(data).decode("ascii")
        components.html("<script>const a=document.createElement('a');a.href="
                        + json.dumps("data:" + mime + ";base64," + encoded)
                        + ";a.download=" + json.dumps(filename)
                        + ";document.body.appendChild(a);a.click();a.remove();</script>", height=0)
        sent.add(token)
        st.caption("ส่งคำสั่งดาวน์โหลดแล้ว หากเบราว์เซอร์บล็อก ให้กดปุ่มดาวน์โหลดด้านบน")
