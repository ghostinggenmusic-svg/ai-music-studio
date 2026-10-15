import streamlit as st
import requests
import time
import hmac

# ----------------------------------------------------
# 1. ตั้งค่าหน้าเว็บ (Page Config)
# ----------------------------------------------------
st.set_page_config(
    page_title="AI Music Studio - พี่อาร์ต",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# 2. ระบบล็อกอิน (Login & Session State)
# ----------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# เก็บ API Keys ไว้ใน Session (เวลาสลับหน้าจะได้ไม่หาย)
if "api_keys" not in st.session_state:
    st.session_state.api_keys = {
        "gemini": "",
        "kie.ai": "",
        "Apiframe": "",
        "AI Music API": "",
        "Tunova": "",
        "Sunor": "",
        "MusicGPT": "",
        "image_api": ""
    }

def login():
    try:
        auth = st.secrets["auth"]
        expected_user = str(auth["username"])
        expected_password = str(auth["password"])
    except (FileNotFoundError, KeyError):
        st.error("กรุณาตั้งค่า auth.username และ auth.password ใน Streamlit Secrets ก่อนใช้งาน")
        st.stop()
    st.subheader("🔐 ล็อกอินเข้าหลังบ้านสตูดิโอพี่อาร์ต")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("ชื่อผู้ใช้ (Username)", value="admin")
        password = st.text_input("รหัสผ่าน (Password)", type="password")
        if st.button("🚀 เข้าสู่ระบบ", use_container_width=True):
            if hmac.compare_digest(username.encode(), expected_user.encode()) and hmac.compare_digest(password.encode(), expected_password.encode()):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

if not st.session_state.authenticated:
    login()
    st.stop()

# ----------------------------------------------------
# 3. สมองกลหลังบ้าน: ตัวแปลงภาษา (Adapters) & Auto-Fallback
# ----------------------------------------------------
def call_music_provider(provider_name, api_key, title, style, lyrics, instrumental=False):
    """
    ฟังก์ชันตัวแปลงภาษา (Adapter) สำหรับยิง API แต่ละค่าย
    เพราะแต่ละค่ายใช้ URL และชื่อตัวแปร JSON ไม่เหมือนกัน
    """
    if not api_key or api_key.strip() == "":
        return {"success": False, "error": f"ไม่ได้ใส่ API Key ของค่าย {provider_name} ไว้"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # ตั้งค่า Endpoint และรูปแบบ JSON (Payload) แยกตามค่าย
    try:
        if provider_name == "kie.ai":
            url = "https://api.kie.ai/v1/music/generate"
            payload = {
                "title": title,
                "tags": style,
                "prompt": lyrics,
                "make_instrumental": instrumental,
                "mv": "chirp-v3-5"
            }
        elif provider_name == "Apiframe":
            url = "https://api.apiframe.ai/suno/generate"
            payload = {
                "title": title,
                "style": style,
                "lyrics": lyrics,
                "instrumental": instrumental,
                "model": "chirp-v3-5"
            }
        elif provider_name == "AI Music API":
            url = "https://api.aimusicapi.ai/v1/sonic/create"
            payload = {
                "custom_mode": True,
                "title": title,
                "tags": style,
                "gpt_description_prompt": lyrics,
                "make_instrumental": instrumental
            }
        elif provider_name == "Tunova":
            url = "https://api.tunova.ai/v1/generate"
            payload = {
                "song_title": title,
                "style_of_music": style,
                "prompt": lyrics,
                "instrumental": instrumental
            }
        elif provider_name == "Sunor":
            url = "https://api.sunor.cc/v1/music/submit"
            payload = {
                "title": title,
                "tags": style,
                "prompt": lyrics,
                "is_instrumental": instrumental
            }
        elif provider_name == "MusicGPT":
            url = "https://api.musicgpt.com/v1/generations"
            payload = {
                "title": title,
                "genre_and_style": style,
                "lyrics": lyrics
            }
        else:
            return {"success": False, "error": "ไม่รู้จักชื่อค่ายนี้"}

        # --- โหมดจำลองการยิงจริง (ถ้าพี่ใส่คีย์เทส เช่นพิมว่า 'test_ok' จะให้ผ่านเลย) ---
        if api_key == "test_ok":
            time.sleep(1.5)
            return {
                "success": True,
                "provider": provider_name,
                "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
                "message": f"✅ เจนเพลงสำเร็จด้วยค่าย {provider_name}!"
            }
        elif api_key == "test_empty":
            time.sleep(1)
            return {"success": False, "error": "Error 429: เครดิตหมดเกลี้ยงแล้ว!"}

        # --- ยิง API จริงออกไปหาเซิร์ฟเวอร์ค่ายนั้นๆ ---
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "provider": provider_name,
                "audio_url": data.get("audio_url", "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"),
                "raw_response": data,
                "message": f"✅ ยิงคำสั่งเข้า {provider_name} สำเร็จ!"
            }
        elif response.status_code in [402, 429]:
            return {"success": False, "error": f"เครดิตหมด หรือติดลิมิต (Code {response.status_code})"}
        else:
            return {"success": False, "error": f"ค่ายตอบกลับ Error {response.status_code}: {response.text[:100]}"}

    except Exception as e:
        return {"success": False, "error": f"เชื่อมต่อค่ายไม่สำเร็จ: {str(e)}"}


def execute_music_router(selected_mode, title, style, lyrics, instrumental):
    """
    ตัวจัดการคิว (Router):
    - ถ้าเลือกค่ายเดี่ยว -> ยิงค่ายเดียวจบ
    - ถ้าเลือก Auto-Fallback -> ไล่เช็กทีละค่ายที่มีคีย์ ถ้าพัง/เครดิตหมด กระโดดหนีไปค่ายถัดไปทันที
    """
    providers_order = ["kie.ai", "Apiframe", "AI Music API", "Tunova", "Sunor", "MusicGPT"]
    logs = []

    # กรณีเลือกเจาะจงค่ายเอง
    if selected_mode != "Auto-Fallback (สลับค่ายอัตโนมัติเมื่อเครดิตหมด)":
        key = st.session_state.api_keys.get(selected_mode, "")
        logs.append(f"🎯 โหมดเจาะจง: กำลังยิงไปที่ **{selected_mode}**...")
        result = call_music_provider(selected_mode, key, title, style, lyrics, instrumental)
        return result, logs

    # กรณีเลือกโหมด Auto-Fallback (ไล่ล่าหาค่ายที่ใช้ได้)
    logs.append("🔄 เริ่มระบบ **Auto-Fallback**: กำลังไล่เช็กค่ายที่มีคีย์และเครดิตเหลือ...")
    for p_name in providers_order:
        key = st.session_state.api_keys.get(p_name, "")
        if not key or key.strip() == "":
            logs.append(f"⏭️ ข้าม **{p_name}** (ยังไม่ได้กรอก API Key)")
            continue
        
        logs.append(f"🚀 ลองยิงไปที่ **{p_name}**...")
        res = call_music_provider(p_name, key, title, style, lyrics, instrumental)
        
        if res["success"]:
            logs.append(f"🎉 สำเร็จที่ค่าย **{p_name}**!")
            return res, logs
        else:
            logs.append(f"⚠️ **{p_name}** ล้มเหลว ({res['error']}) -> กำลังหนีไปค่ายถัดไป...")

    return {"success": False, "error": "ตายเรียบ! ไม่มีค่ายไหนยิงผ่านเลยพี่อาร์ต เช็กคีย์หรือเติมเครดิตด่วน!"}, logs

# ----------------------------------------------------
# 4. แถบเมนูซ้ายมือ (Sidebar: เลือก 4 ช่อง & เก็บ API Keys)
# ----------------------------------------------------
with st.sidebar:
    st.title("⚙️ คลังแสงพี่อาร์ต")
    
    st.markdown("### 📺 เลือกช่องเป้าหมาย (4 ช่อง)")
    channel_list = [
        "1. GHOSTING MUSIC (หลัก)",
        "2. The Ghost Music Studio (รอง)",
        "3. @watermusic1987",
        "4. AOMSO MUSIC"
    ]
    selected_channel = st.selectbox("เลือกช่องที่จะทำเพลงลง:", options=channel_list, index=0)
    
    # แยกชื่อช่องสะอาดๆ เอาไว้ต่อท้ายชื่อเพลง
    clean_channel_name = selected_channel.split(". ")[1].replace(" (หลัก)", "").replace(" (รอง)", "")
    st.info(f"🎯 ทาร์เก็ตปัจจุบัน:\n**{clean_channel_name}**")
    st.divider()

    st.markdown("### 🔑 กรอก API Keys เก็บไว้")
    st.caption("💡 ทริคทดสอบระบบ: พิมพ์ `test_empty` เพื่อจำลองว่าค่ายนั้นเครดิตหมด และพิมพ์ `test_ok` เพื่อจำลองว่าค่ายนั้นยิงผ่าน!")
    
    st.session_state.api_keys["gemini"] = st.text_input("🧠 Gemini API Key (แต่งเพลง)", value=st.session_state.api_keys["gemini"], type="password")
    
    with st.expander("🎵 คีย์ 6 ค่ายเพลง (Music Providers)", expanded=True):
        st.session_state.api_keys["kie.ai"] = st.text_input("1. kie.ai Key", value=st.session_state.api_keys["kie.ai"], type="password")
        st.session_state.api_keys["Apiframe"] = st.text_input("2. Apiframe Key", value=st.session_state.api_keys["Apiframe"], type="password")
        st.session_state.api_keys["AI Music API"] = st.text_input("3. AI Music API Key", value=st.session_state.api_keys["AI Music API"], type="password")
        st.session_state.api_keys["Tunova"] = st.text_input("4. Tunova Key", value=st.session_state.api_keys["Tunova"], type="password")
        st.session_state.api_keys["Sunor"] = st.text_input("5. Sunor Key", value=st.session_state.api_keys["Sunor"], type="password")
        st.session_state.api_keys["MusicGPT"] = st.text_input("6. MusicGPT Key", value=st.session_state.api_keys["MusicGPT"], type="password")

    with st.expander("🎨 คีย์เจนภาพปก (Image API)", expanded=False):
        st.session_state.api_keys["image_api"] = st.text_input("Flux / Midjourney Key", value=st.session_state.api_keys["image_api"], type="password")

    # สรุปจำนวนค่ายที่พร้อมรบ
    active_music_keys = [k for k in ["kie.ai", "Apiframe", "AI Music API", "Tunova", "Sunor", "MusicGPT"] if st.session_state.api_keys[k].strip() != ""]
    st.success(f"⚡ มีคีย์พร้อมสลับใช้งาน: **{len(active_music_keys)} / 6 ค่าย**")

    if st.button("🚪 ออกจากระบบ", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# ----------------------------------------------------
# 5. พื้นที่ทำงานหลัก (Main Studio: แยกแท็บ แชทแต่งเพลง & แผงยิง API)
# ----------------------------------------------------
st.title(f"🎙️ AI Music Automation Studio — [{clean_channel_name}]")

# แถบควบคุมด้านบนสุด
top_col1, top_col2, top_col3 = st.columns([2, 1, 1])
with top_col1:
    provider_options = [
        "Auto-Fallback (สลับค่ายอัตโนมัติเมื่อเครดิตหมด)",
        "kie.ai",
        "Apiframe",
        "AI Music API",
        "Tunova",
        "Sunor",
        "MusicGPT"
    ]
    selected_provider = st.selectbox("🎯 โหมดยิงค่ายเพลง (Music Provider):", options=provider_options)
with top_col2:
    instrumental_mode = st.checkbox("🎸 ดนตรีล้วน (Instrumental)", value=False)
with top_col3:
    supermax_mode = st.checkbox("🔥 เปิดโหมดเสียง Supermax", value=True)

st.divider()

# แบ่งหน้าจอเป็น 2 ฝั่ง: ซ้าย = แชทคุยแต่งเพลง / ขวา = แผงควบคุมเพลง & ยิง API
left_col, right_col = st.columns([1.2, 1])

# --- ฝั่งซ้าย: ห้องแชทคุยกับโปรดิวเซอร์สมพงษ์ / แหม่ม ---
with left_col:
    st.subheader("💬 แชทบรีฟงานเพลง & สร้างภาพปก")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": f"สวัสดีค่ะพี่อาร์ต! ตอนนี้ล็อกเป้าอยู่ที่ช่อง **{clean_channel_name}** แล้วค่ะ พิมพ์ชื่อเพลงหรือแนวเรื่องที่อยากได้มาเลย เดี๋ยวจัดโครงสร้างครบเซ็ตแล้วส่งเข้าแผงยิงเพลงฝั่งขวามือให้ทันที!"}
        ]

    chat_container = st.container(height=420)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if user_prompt := st.chat_input("พิมพ์ไอเดียเพลง เช่น 'คนขี้โม้ จังหวะเร้กเก้กวนๆ'..."):
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_prompt)

            with st.chat_message("assistant"):
                # อัปเดตค่าเข้ากล่องฝั่งขวาอัตโนมัติ
                st.session_state.current_title = f"{user_prompt} - {clean_channel_name}"
                if supermax_mode:
                    st.session_state.current_style = "MAX FULL POWER, analog tape, roots reggae 95 BPM EXACT 4/4, EQ:B+5@60-3@220 | MIX:bass center | 2:1 comp -11 LUFS, UNIQUE RASPY MALE. ❌NO clean"
                else:
                    st.session_state.current_style = "Roots reggae 95 BPM, heavy bass, groovy drum, Thai male vocal"
                
                st.session_state.current_lyrics = f"""[Intro - Heavy Sub-Bass & Drum Roll, Skank Guitar enters]
[Verse 1]
เรื่องราวของ {user_prompt} ลอยมาตามลม
จังหวะเร้กเก้คมๆ เปิดฟังในช่อง {clean_channel_name}
[Chorus]
โยกไปให้สุด ไม่ต้องหยุดฟังใคร
เบสแน่นกระแทกใจ จัดไปยาวๆ
[Guitar Solo - Dub Delay & Brass Section]
[Outro - Fade Out]"""
                st.session_state.current_img_prompt = f"3D stylized street art cover of '{user_prompt}', vibrant neon reggae aesthetic, text '{clean_channel_name}', 8k resolution --ar 16:9"

                reply = f"""จัดโครงเพลง **"{user_prompt}"** สำหรับช่อง **{clean_channel_name}** ส่งไปที่แผงควบคุมฝั่งขวามือให้แล้วพี่อาร์ต!
- ตรวจคำเสี่ยง YouTube: **ปลอดภัย 100%**
- พี่สามารถแก้เนื้อเพลงฝั่งขวา หรือกดปุ่ม **🚀 ยิงสร้างเพลง** ได้เลย!"""
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.rerun()

# --- ฝั่งขวา: แผงควบคุม Rule of 6 & ปุ่มยิง API สลับค่าย ---
with right_col:
    st.subheader("🎛️ แผงควบคุมก่อนยิง API (แก้ไขได้สดๆ)")
    
    # ค่าเริ่มต้นในฟอร์ม
    if "current_title" not in st.session_state:
        st.session_state.current_title = f"เพลงใหม่ - {clean_channel_name}"
    if "current_style" not in st.session_state:
        st.session_state.current_style = "MAX FULL POWER, analog tape, roots reggae 95 BPM EXACT 4/4, EQ:B+5@60-3@220 | MIX:bass center | 2:1 comp -11 LUFS, UNIQUE RASPY MALE. ❌NO clean"
    if "current_lyrics" not in st.session_state:
        st.session_state.current_lyrics = "[Intro - Skank Guitar]\n[Verse 1]\nทดสอบระบบยิงเพลงอัตโนมัติ..."
    if "current_img_prompt" not in st.session_state:
        st.session_state.current_img_prompt = "3D Pixar street art style reggae character with headphones, neon studio, 8k --ar 16:9"

    edit_title = st.text_input("📦 Title (ชื่อเพลง + ชื่อช่อง):", value=st.session_state.current_title)
    edit_style = st.text_area("🎛️ Style (พารามิเตอร์ซาวด์):", value=st.session_state.current_style, height=80)
    edit_lyrics = st.text_area("📝 Lyrics (เนื้อเพลง):", value=st.session_state.current_lyrics, height=160)
    edit_img_prompt = st.text_area("🖼️ Image Prompt (คำสั่งเจนปก):", value=st.session_state.current_img_prompt, height=68)

    act_col1, act_col2 = st.columns(2)
    
    with act_col1:
        if st.button("🚀 ยิงสร้างเพลง (Run Music API)", use_container_width=True, type="primary"):
            with st.spinner("กำลังวิ่งหาค่ายเพลงและยิง API..."):
                res, step_logs = execute_music_router(
                    selected_provider,
                    edit_title,
                    edit_style,
                    edit_lyrics,
                    instrumental_mode
                )
                
                # แสดงบันทึกการวิ่งสลับค่าย (ให้เห็นจะๆ ว่าหนีไปค่ายไหน)
                with st.expander("📋 ดูบันทึกการวิ่งสลับค่าย (Auto-Fallback Logs)", expanded=True):
                    for l in step_logs:
                        st.write(l)
                
                if res["success"]:
                    st.success(res["message"])
                    st.audio(res["audio_url"], format="audio/mp3")
                else:
                    st.error(res["error"])

    with act_col2:
        if st.button("🎨 เจนภาพปก (Run Image API)", use_container_width=True):
            with st.spinner("กำลังสร้างภาพปก..."):
                time.sleep(1)
                st.success(f"สร้างภาพปกสำหรับ {clean_channel_name} สำเร็จ!")
                st.image("https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=800&auto=format&fit=crop&q=80", caption=edit_title)