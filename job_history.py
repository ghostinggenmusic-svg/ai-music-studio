"""Account-scoped job metadata. Never persist credentials or raw API payloads."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import streamlit as st

DB = Path(__file__).parent / ".studio-data" / "history.sqlite3"

def connect():
    DB.parent.mkdir(exist_ok=True)
    db = sqlite3.connect(DB, timeout=10)
    db.execute("CREATE TABLE IF NOT EXISTS jobs (owner TEXT, job TEXT, updated TEXT, title TEXT, provider TEXT, status TEXT, urls TEXT, PRIMARY KEY(owner, job))")
    return db

def record(job, title, provider, status, urls=None):
    owner = st.session_state.get("login_username")
    if not owner:
        return
    with connect() as db:
        db.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?) ON CONFLICT(owner,job) DO UPDATE SET updated=excluded.updated, status=excluded.status, urls=excluded.urls",
                   (owner, job, datetime.now(timezone.utc).isoformat(), title, provider, status, json.dumps(urls or [])))

def render():
    with st.expander("📚 ประวัติงานเพลง", expanded=False):
        st.caption("ประวัติแยกตามบัญชี • อยู่หลังรีเฟรชได้ แต่พื้นที่ Streamlit อาจถูกล้างเมื่อรีสตาร์ตหรือ Deploy • ดาวน์โหลดประวัติเก็บสำรองไว้ • ลิงก์ไฟล์ของค่ายอาจหมดอายุ")
        with connect() as db:
            db.row_factory = sqlite3.Row
            rows = [dict(r) for r in db.execute("SELECT * FROM jobs WHERE owner=? ORDER BY updated DESC LIMIT 200", (st.session_state.get("login_username", ""),))]
        if not rows:
            st.info("ยังไม่มีงานที่บันทึกหลังเปิดใช้ประวัติ")
        else:
            st.download_button("ดาวน์โหลดประวัติ JSON", json.dumps(rows, ensure_ascii=False, indent=2), file_name="studio-history.json", mime="application/json")
            for row in rows:
                st.markdown("**" + row["title"] + "**")
                st.write(row["provider"] + " · " + row["status"])
                for i, url in enumerate(json.loads(row["urls"])):
                    if isinstance(url, str) and url.startswith("https://"):
                        st.link_button("เปิดไฟล์เพลง " + str(i + 1), url)
