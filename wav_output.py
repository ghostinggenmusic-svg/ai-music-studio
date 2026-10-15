"""Provider-side WAV preference. Never transcodes MP3 locally or renames files."""
from urllib.parse import urlparse
import requests
import streamlit as st

SUPPORTED=('kie.ai','AI Music API','MusicGPT')
NOTES={
 'MusicGPT':'WAV เป็นค่าเริ่มต้นจากลิงก์ conversion_path_wav ของค่าย',
 'kie.ai':'WAV เป็นค่าเริ่มต้น: สร้างเพลงแล้วส่งงานขอ WAV เพิ่ม อาจใช้เครดิตเพิ่มตามราคาค่าย',
 'AI Music API':'WAV เป็นค่าเริ่มต้น: ขอไฟล์หลังเพลงเสร็จ ค่าขอ WAV 2 เครดิตต่อเพลง (2 เวอร์ชัน = เพิ่ม 4 เครดิต)',
 'crun.ai':'ยังไม่พบตัวเลือก WAV ในเอกสาร Suno ของ Crun — ใช้ไฟล์ที่ค่ายส่งกลับ',
 'Apiframe':'ยังไม่พบพารามิเตอร์ WAV ในเอกสาร Suno ที่ตรวจ — ใช้รูปแบบเดิม',
 'Tunova':'ยังไม่พบตัวเลือก WAV ในเอกสารที่ตรวจ — ใช้รูปแบบเดิม',
 'Sunor':'ยังไม่พบตัวเลือก WAV ในเอกสารที่ตรวจ — ใช้รูปแบบเดิม',
}

def headers(provider,key):
    return {'Authorization':key} if provider=='MusicGPT' else {'Authorization':'Bearer '+key}

def request(provider,key,method,url,**kwargs):
    r=requests.request(method,url,headers=headers(provider,key),timeout=30,**kwargs)
    if r.status_code==202 and url.endswith('/sonic/download'): return {'processing':True}
    if r.status_code not in (200,202): raise ValueError('HTTP '+str(r.status_code))
    data=r.json()
    if not isinstance(data,dict): raise ValueError('ข้อมูลไม่ถูกต้อง')
    if data.get('code',200)!=200 or data.get('success') is False: raise ValueError('API ปฏิเสธคำขอ code '+str(data.get('code',data.get('error_code','?'))))
    return data

def submit(provider,key,title,style,lyrics,instrumental,wav=True):
    old=st.session_state.get('wav_music_job')
    if old and old.get('state') not in ('complete','failed'):
        return {'success':True,'pending':True,'message':'มีงานที่รอผลอยู่ ตรวจสถานะด้านล่างก่อนส่งงานใหม่'}
    job={'provider':provider,'wav':wav,'state':'submitting','tracks':[]}
    st.session_state.wav_music_job=job
    try:
        if provider=='kie.ai':
            payload={'title':title,'style':style,'lyrics':'' if instrumental else lyrics,'customMode':True,'instrumental':instrumental,'model':'V6','duration':212}
            data=request(provider,key,'POST','https://api.kie.ai/api/v1/generate',json=payload)
            task=(data.get('data') or {}).get('taskId')
        elif provider=='AI Music API':
            payload={'custom_mode':True,'title':title,'tags':style,'prompt':'' if instrumental else lyrics,'make_instrumental':instrumental,'mv':'chirp-v6','task_type':'create_music'}
            data=request(provider,key,'POST','https://api.aimusicapi.ai/api/v1/sonic/create',json=payload)
            task=data.get('task_id') or (data.get('data') or {}).get('task_id')
        else:
            payload={'prompt':title+'; '+style,'music_style':style,'lyrics':'' if instrumental else lyrics,'make_instrumental':instrumental}
            data=request(provider,key,'POST','https://api.musicgpt.com/api/public/v2/MusicAI',json=payload)
            task=data.get('task_id')
        if not task: raise ValueError('ไม่พบ task ID')
        job.update(task_id=task,state='generating')
        return {'success':True,'pending':True,'provider':provider,'message':'รับงานแล้ว กดตรวจสถานะเพลง / WAV ด้านล่าง ไม่ต้องส่งสร้างซ้ำ'}
    except (requests.RequestException,ValueError,TypeError):
        job['state']='uncertain'
        return {'success':True,'pending':True,'message':'ยังยืนยันการรับงานไม่ได้ ตรวจ Logs ของค่ายก่อนส่งซ้ำ เพื่อหลีกเลี่ยงเครดิตซ้ำ'}

def poll(job,key):
    p=job['provider']; task=job.get('task_id')
    if not task or job['state'] in ('complete','failed'): return
    if job['state']=='generating':
        if p=='kie.ai':
            data=request(p,key,'GET','https://api.kie.ai/api/v1/generate/record-info',params={'taskId':task})['data']
            status=data.get('status')
            if status in ('CREATE_TASK_FAILED','GENERATE_AUDIO_FAILED','SENSITIVE_WORD_ERROR','CALLBACK_EXCEPTION'):
                job.update(state='failed',error='ค่ายสร้างเพลงไม่สำเร็จ: '+status); return
            if status!='SUCCESS': return
            job['tracks']=[{'id':x['id'],'audio':x.get('audio_url') or x.get('audioUrl'),'state':'new'} for x in data.get('response',{}).get('sunoData',[])]
        elif p=='AI Music API':
            body=request(p,key,'GET','https://api.aimusicapi.ai/api/v1/sonic/task/'+task)
            data=body.get('data')
            if body.get('status')=='failed' or (isinstance(data,dict) and data.get('state')=='failed'):
                job.update(state='failed',error='ค่ายแจ้งว่าสร้างเพลงล้มเหลว'); return
            if isinstance(data,list) and any(x.get('state')=='failed' for x in data):
                job.update(state='failed',error='ค่ายแจ้งว่าสร้างเพลงล้มเหลว'); return
            if not isinstance(data,list) or not data: return
            if any(x.get('state') not in ('succeeded','complete') for x in data): return
            job['tracks']=[{'id':x['clip_id'],'audio':x.get('audio_url'),'state':'new'} for x in data]
        else:
            body=request(p,key,'GET','https://api.musicgpt.com/api/public/v1/byId',params={'conversionType':'MUSIC_AI','task_id':task})
            data=body.get('conversion') or {}
            if data.get('status') in ('FAILED','ERROR'):
                job.update(state='failed',error='MusicGPT แจ้งว่าสร้างเพลงล้มเหลว'); return
            if data.get('status')!='COMPLETED': return
            job['tracks']=[{'id':str(i),'audio':data.get('conversion_path_'+str(i)),'wav':data.get('conversion_path_wav_'+str(i)),'state':'done'} for i in (1,2) if data.get('conversion_path_'+str(i)) or data.get('conversion_path_wav_'+str(i))]
        if not job['tracks']:
            job.update(state='failed',error='งานเสร็จแต่ไม่พบเพลง ตรวจหน้า Logs ของค่าย'); return
        job['state']='wav' if job['wav'] and p!='MusicGPT' else 'complete'
    if job['state']=='wav':
        for track in job['tracks']:
            if track['state']=='new':
                # Mark before posting: network failures cannot trigger duplicate paid conversions.
                track['state']='uncertain'
                if p=='kie.ai':
                    body=request(p,key,'POST','https://api.kie.ai/api/v1/wav/generate',json={'taskId':task,'audioId':track['id']})
                    track['wav_task']=(body.get('data') or {}).get('taskId')
                    track['state']='pending' if track['wav_task'] else 'uncertain'
                else:
                    body=request(p,key,'POST','https://api.aimusicapi.ai/api/v1/sonic/download',json={'clip_id':track['id'],'formats':['mp3','wav']})
                    if body.get('processing'):
                        track['state']='download_pending'
                    else:
                        track['wav']=next((x.get('file_url') for x in (body.get('data') or {}).get('files',[]) if x.get('format')=='wav'),None)
                        track['state']='done' if track['wav'] else 'uncertain'
            elif track['state']=='download_pending':
                track['state']='uncertain'
                body=request(p,key,'POST','https://api.aimusicapi.ai/api/v1/sonic/download',json={'clip_id':track['id'],'formats':['mp3','wav']})
                if body.get('processing'): track['state']='download_pending'
                else:
                    track['wav']=next((x.get('file_url') for x in (body.get('data') or {}).get('files',[]) if x.get('format')=='wav'),None)
                    track['state']='done' if track['wav'] else 'uncertain'
            elif track['state']=='pending':
                data=request(p,key,'GET','https://api.kie.ai/api/v1/wav/record-info',params={'taskId':track['wav_task']})['data']
                status=data.get('successFlag')
                if status=='SUCCESS':
                    track['wav']=(data.get('response') or {}).get('audioWavUrl'); track['state']='done' if track['wav'] else 'uncertain'
                elif status not in ('PENDING',None): track['state']='failed'
        if all(x['state'] in ('done','failed','uncertain') for x in job['tracks']): job['state']='complete'

def render_jobs(keys):
    job=st.session_state.get('wav_music_job')
    if not job: return
    st.subheader('🎵 งานเพลง / WAV — '+job['provider'])
    if job.get('task_id'): st.code(job['task_id'],language=None)
    if st.button('🔄 ตรวจสถานะเพลง / WAV'):
        try: poll(job,keys.get(job['provider'],''))
        except (requests.RequestException,ValueError,KeyError,TypeError) as e:
            st.warning('ตรวจไม่สำเร็จ งานเดิมยังถูกเก็บไว้ กรุณาดู Logs ก่อนส่งซ้ำ')
    if job['state']=='failed': st.error(job.get('error','งานล้มเหลว'))
    elif job['state']=='uncertain': st.warning('ยังยืนยันการส่งงานไม่ได้ ดู Logs ของค่ายก่อนสร้างซ้ำ')
    elif job['state']!='complete': st.info('กำลังรอเพลงหรือไฟล์ WAV รอ 15–30 วินาทีแล้วตรวจอีกครั้ง')
    for i,track in enumerate(job['tracks'],1):
        preferred=track.get('wav') if job['wav'] else track.get('audio')
        url=preferred or track.get('audio') or track.get('wav')
        if not isinstance(url,str) or urlparse(url).scheme!='https': continue
        is_wav=bool(track.get('wav') and url==track['wav'])
        st.audio(url,format='audio/wav' if is_wav else 'audio/mp3')
        st.link_button(('ดาวน์โหลด WAV' if is_wav else 'เปิดไฟล์เสียงเดิม')+' เวอร์ชัน '+str(i),url)
        if job['wav'] and not is_wav: st.caption('ยังไม่ได้ WAV ของเวอร์ชันนี้ เก็บไฟล์เดิมไว้ ไม่มีการแปลง MP3 ในแอป')
