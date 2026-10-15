"""Read-only credential and balance checks; never creates generation jobs."""
from datetime import datetime, timezone
import hashlib
from decimal import Decimal, InvalidOperation
import requests
import streamlit as st


def check_api(provider, key, credits=False):
    key = key.strip()
    if not key:
        return {'ok':False,'message':'กรุณาใส่ API Key ก่อนตรวจสอบ'}
    if key in ('test_ok','test_empty'):
        return {'ok':False,'message':'นี่คือคีย์จำลอง ไม่สามารถตรวจการเชื่อมต่อหรือเครดิตจริงได้'}
    if provider not in ('gemini', 'crun.ai'):
        return {'ok':False,'message':'ยังไม่รองรับการตรวจค่ายนี้ ต้องเชื่อม API ตรวจบัญชีของค่ายก่อน'}
    if provider == 'gemini' and credits:
        return {'ok':None,'message':'Gemini ใช้โควตาของโปรเจกต์ ดูยอดใช้และโควตาจริงใน Google AI Studio', 'url':'https://aistudio.google.com/usage'}
    try:
        if provider == 'gemini':
            response=requests.get('https://generativelanguage.googleapis.com/v1beta/models', headers={'x-goog-api-key':key}, params={'pageSize':100}, timeout=15)
        else:
            response=requests.get('https://api.crun.ai/api/v1/client/account/balance', headers={'X-API-KEY':key}, timeout=15)
        if response.status_code != 200:
            return {'ok':False,'message':f'ตรวจไม่ผ่าน HTTP {response.status_code} — ตรวจคีย์ สิทธิ์ หรือการจำกัดการเรียก'}
        data=response.json()
        if provider == 'gemini':
            if not isinstance(data.get('models'), list):
                raise ValueError('missing model list')
            return {'ok':True,'message':'เชื่อมต่อ Gemini สำเร็จ อ่านรายชื่อโมเดลได้ (ยังไม่ยืนยันโควตาสร้างข้อความ)'}
        if data.get('code') != 200:
            return {'ok':False,'message':f"Crun ปฏิเสธการตรวจบัญชี (code {data.get('code')})"}
        balance=(data.get('data') or {}).get('balance')
        if balance is None or isinstance(balance,bool):
            raise ValueError('missing balance')
        amount=Decimal(str(balance))
        if not amount.is_finite():
            raise ValueError('invalid balance')
        return {'ok':True,'message':f'เชื่อมต่อ Crun สำเร็จ • เครดิตคงเหลือ {amount:,f}', 'balance':str(amount)}
    except (requests.RequestException, ValueError, InvalidOperation, TypeError):
        return {'ok':False,'message':'ตรวจไม่สำเร็จ: เชื่อมต่อไม่ได้หรือรูปแบบข้อมูลไม่ถูกต้อง ลองใหม่อีกครั้ง'}


def render_checks(keys):
    st.markdown('### 🔌 ตรวจ API และเครดิต')
    provider=st.selectbox('เลือก API ที่จะตรวจ', ['gemini','crun.ai','kie.ai','Apiframe','AI Music API','Tunova','Sunor','MusicGPT'], format_func=lambda x:'Gemini' if x=='gemini' else x, key='check_provider')
    key=keys.get(provider,'').strip()
    fingerprint=hashlib.sha256(key.encode()).hexdigest()
    a,b=st.columns(2)
    connect=a.button('🔌 เช็กการเชื่อมต่อ', use_container_width=True)
    credits=b.button('💳 เช็กเครดิต', use_container_width=True)
    st.caption('ตรวจบัญชีเท่านั้น ไม่ส่งสร้างเพลงหรือสร้างข้อความ')
    if connect or credits:
        with st.spinner('กำลังตรวจ API...'):
            result=check_api(provider,key,credits=credits)
        st.session_state.api_check_result={'provider':provider,'fingerprint':fingerprint,'result':result,'time':datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}
    saved=st.session_state.get('api_check_result')
    if saved and saved['provider']==provider and saved['fingerprint']==fingerprint:
        result=saved['result']
        if result['ok'] is True: st.success(result['message'])
        elif result['ok'] is False: st.error(result['message'])
        else: st.info(result['message'])
        st.caption('ตรวจล่าสุด: '+saved['time'])
        if result.get('url'): st.link_button('เปิดโควตาและยอดใช้ Gemini',result['url'])
