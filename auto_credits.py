"""Session-local auto refresh for the Crun credit balance."""
import hashlib
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st
from api_checks import check_api


def refresh_balance(key, saved, task_marker, force=False, now=None):
    now=time.monotonic() if now is None else now
    fingerprint=hashlib.sha256(key.encode()).hexdigest()
    if not force and saved and saved['fingerprint']==fingerprint and saved['task_marker']==task_marker and now-saved['checked_at']<60:
        return saved
    result=check_api('crun.ai',key,credits=True)
    return {'fingerprint':fingerprint,'task_marker':task_marker,'checked_at':now,'result':result,
            'time':datetime.now(ZoneInfo('Asia/Bangkok')).strftime('%H:%M:%S')}


@st.fragment(run_every=60)
def render_auto_credits():
    if not st.session_state.get('authenticated'):
        return
    key=st.session_state.get('api_keys',{}).get('crun.ai','').strip()
    st.markdown('### 💳 เครดิต Crun อัตโนมัติ')
    if not key or key in ('test_ok','test_empty'):
        st.session_state.pop('auto_crun_balance',None)
        st.caption('ใส่ crun.ai Key จริงแล้วกด Enter เพื่อแสดงเครดิต')
        return
    force=st.button('🔄 รีเฟรชเครดิตตอนนี้',key='refresh_auto_crun')
    task=st.session_state.get('crun_task') or {}
    marker=(task.get('task_id'),task.get('pending'),task.get('success'))
    saved=refresh_balance(key,st.session_state.get('auto_crun_balance'),marker,force)
    st.session_state.auto_crun_balance=saved
    result=saved['result']
    if result.get('ok') and 'balance' in result:
        st.metric('เครดิตคงเหลือ',result['balance'])
    else:
        st.warning(result['message'])
    st.caption('ตรวจล่าสุด '+saved['time']+' น. • อัปเดตทุก 60 วินาทีขณะเปิดเว็บ')
    st.caption('Gemini: ดูโควตาใน Google AI Studio ผ่านปุ่มเช็กเครดิตด้านล่าง')
