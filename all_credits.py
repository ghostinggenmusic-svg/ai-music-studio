"""Read-only balances for all configured providers. No generation requests."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import time
from zoneinfo import ZoneInfo
import requests
import streamlit as st
from api_checks import check_api

NAMES={'gemini':'Gemini','kie.ai':'kie.ai','Apiframe':'Apiframe','AI Music API':'AI Music API','Tunova':'Tunova','Sunor':'Sunor','MusicGPT':'MusicGPT','crun.ai':'crun.ai','image_api':'API เจนภาพ'}
# Official provider docs verified before adding these read-only routes.
ROUTES={
 'kie.ai':('https://api.kie.ai/api/v1/chat/credit','bearer'),
 'Apiframe':('https://api.apiframe.ai/v2/me','key'),
 'AI Music API':('https://api.aimusicapi.ai/api/v1/get-credits','bearer'),
 'Tunova':('https://api.tunova.ai/api/balance','key'),
 'Sunor':('https://sunor.cc/api/v1/account/balance','key'),
}

def amount(value):
    if value is None or isinstance(value,bool): raise ValueError('missing balance')
    number=Decimal(str(value))
    if not number.is_finite(): raise ValueError('invalid balance')
    return number

def provider_balance(provider,key):
    key=key.strip()
    if not key: return {'ok':None,'message':'ยังไม่ใส่คีย์'}
    if key in ('test_ok','test_empty'): return {'ok':None,'message':'คีย์จำลอง — ไม่มีเครดิตจริง'}
    if provider=='gemini':
        result=check_api('gemini',key)
        if result.get('ok'): result.update(message='เชื่อมต่อแล้ว • ดูโควตาใน AI Studio',url='https://aistudio.google.com/usage')
        return result
    if provider=='crun.ai': return check_api(provider,key,credits=True)
    if provider=='MusicGPT': return {'ok':None,'message':'ยังดึงยอดผ่าน API ไม่ได้ — ตรวจในบัญชี MusicGPT','url':'https://musicgpt.com/'}
    if provider=='image_api': return {'ok':None,'message':'ยังดึงยอดไม่ได้ — ต้องระบุผู้ให้บริการของคีย์เจนภาพก่อน'}
    if provider not in ROUTES: return {'ok':None,'message':'ยังไม่รองรับผู้ให้บริการนี้'}
    url,auth=ROUTES[provider]
    headers={'Authorization':'Bearer '+key} if auth=='bearer' else {'X-API-Key':key}
    try:
        response=requests.get(url,headers=headers,timeout=12)
        if response.status_code!=200:
            return {'ok':False,'message':f'ตรวจไม่ผ่าน HTTP {response.status_code} — ตรวจคีย์หรือสิทธิ์'}
        body=response.json()
        if not isinstance(body,dict): raise ValueError('invalid response')
        if body.get('code',200)!=200: return {'ok':False,'message':f"ตรวจไม่ผ่าน code {body.get('code')}"}
        if provider=='kie.ai': value=body.get('data')
        elif provider=='Apiframe': value=(body.get('team') or {}).get('credits')
        elif provider=='AI Music API':
            data=body.get('data',body)
            value=amount(data.get('credits'))+amount(data.get('extra_credits'))
        elif provider=='Tunova': value=body.get('available') if body.get('available') is not None else body.get('token_balance')
        elif provider=='Sunor': value=(body.get('data') or {}).get('available')
        value=amount(value)
        return {'ok':True,'balance':str(value),'unit':'tokens' if provider=='Tunova' else 'เครดิต','message':'ตรวจยอดสำเร็จ'}
    except (requests.RequestException,ValueError,TypeError,InvalidOperation,AttributeError):
        return {'ok':False,'message':'ดึงยอดไม่ได้ — เชื่อมต่อล้มเหลวหรือข้อมูลไม่ตรงรูปแบบ'}

def collect_balances(keys,cache,task_marker,force=False,now=None):
    now=time.monotonic() if now is None else now
    active={p:k.strip() for p,k in keys.items() if k.strip()}
    updated={p:entry for p,entry in cache.items() if p in active}
    due={}
    for provider,key in active.items():
        fingerprint=hashlib.sha256(key.encode()).hexdigest()
        marker=task_marker if provider=='crun.ai' else None
        old=updated.get(provider)
        if force or not old or old['fingerprint']!=fingerprint or old['task_marker']!=marker or now-old['checked_at']>=60:
            due[provider]=(key,fingerprint,marker)
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures={p:pool.submit(provider_balance,p,info[0]) for p,info in due.items()}
        for provider,future in futures.items():
            result=future.result()
            updated[provider]={'fingerprint':due[provider][1],'task_marker':due[provider][2],'checked_at':now,'result':result,'time':datetime.now(ZoneInfo('Asia/Bangkok')).strftime('%H:%M:%S')}
    return updated

@st.fragment(run_every=60)
def render_all_credits():
    if not st.session_state.get('authenticated'): return
    keys=st.session_state.get('api_keys',{})
    st.markdown('### 💳 เครดิตทุก API ที่ใส่ไว้')
    force=st.button('🔄 รีเฟรชเครดิตทุกค่าย',key='refresh_all_balances')
    confirmed=st.session_state.pop('confirm_keys_check',False)
    force=force or confirmed
    task=st.session_state.get('crun_task') or {}
    marker=(task.get('task_id'),task.get('pending'),task.get('success'))
    cache=collect_balances(keys,st.session_state.get('provider_balances',{}),marker,force)
    st.session_state.provider_balances=cache
    if st.session_state.get('show_key_receipt') and cache:
        receipt=[]
        for provider,entry in cache.items():
            result=entry['result']
            label=NAMES[provider]
            if result.get('ok') and 'balance' in result:
                receipt.append('✅ '+label+' — รับคีย์แล้ว • เครดิตคงเหลือ '+result['balance']+' '+result.get('unit','เครดิต'))
            elif result.get('ok'):
                receipt.append('✅ '+label+' — รับคีย์แล้ว • '+result['message'])
            else:
                receipt.append(('⚠️ ' if result.get('ok') is False else 'ℹ️ ')+label+' — รับค่าคีย์แล้ว • '+result['message'])
        st.info('**ผลยืนยันคีย์และเครดิต**\n\n'+'\n\n'.join(receipt))
    if not cache: st.caption('ใส่ API Key แล้วกดปุ่มยืนยันคีย์และเช็กเครดิต')
    for provider in NAMES:
        if provider not in cache: continue
        entry=cache[provider]; result=entry['result']
        st.markdown('**'+NAMES[provider]+'**')
        if result.get('ok') and 'balance' in result:
            st.metric('คงเหลือ',result['balance']+' '+result.get('unit','เครดิต'))
        elif result.get('ok') is False: st.error(result['message'])
        else: st.caption(result['message'])
        if result.get('url'): st.link_button('เปิดบัญชี '+NAMES[provider],result['url'])
        st.caption('ตรวจล่าสุด '+entry['time']+' น.')
    st.caption('อัปเดตทุก 60 วินาทีขณะเปิดเว็บ • เครดิตแต่ละค่ายแยกกัน • ไม่สร้างเพลงเพิ่ม')
