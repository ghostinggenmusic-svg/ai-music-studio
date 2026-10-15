"""Crun Suno adapter. Docs: https://docs.crun.ai/suno-api/generate-music"""
import requests

BASE = 'https://api.crun.ai/api/v1/client/job/'

def create_music(key, title, style, lyrics, instrumental=False):
    if not key:
        return {'success': False, 'error': 'กรุณาใส่ crun.ai API Key'}
    payload = {'model': 'suno/music-generate', 'callback_url': '', 'input': {
        'mode': 'custom', 'model': 'v6', 'instrumental': instrumental,
        'title': title, 'tags': style, 'lyrics': '' if instrumental else lyrics}}
    try:
        response = requests.post(BASE + 'CreateTask', headers={'X-API-KEY': key}, json=payload, timeout=30)
        data = response.json()
        if response.status_code != 200 or data.get('code') != 200:
            return {'success': False, 'error': f"Crun ปฏิเสธงาน (HTTP {response.status_code}, code {data.get('code')})"}
        task_id = (data.get('data') or {}).get('task_id')
        if not task_id:
            return {'success': False, 'error': 'Crun ไม่ได้ส่ง task_id กลับมา ตรวจหน้า Logs ก่อนส่งซ้ำ'}
        return {'success': True, 'pending': True, 'provider': 'crun.ai', 'task_id': task_id,
                'message': 'Crun รับงานแล้ว ยังไม่ได้เพลง กดตรวจสถานะด้านล่างเพื่อรับผล'}
    except (requests.RequestException, ValueError):
        # A submission may have succeeded upstream. Stop the router to avoid charging a second provider.
        return {'success': True, 'pending': False, 'provider': 'crun.ai',
                'message': 'ยังยืนยันการส่งงานไม่ได้ ตรวจ Logs ที่ crun.ai ก่อนกดสร้างซ้ำ เพื่อป้องกันการใช้เครดิตซ้ำ'}

def check_music(key, task_id):
    result = {'success': True, 'pending': True, 'provider': 'crun.ai', 'task_id': task_id}
    try:
        response = requests.get(BASE + 'TaskInfo', headers={'X-API-KEY': key}, params={'task_id': task_id}, timeout=30)
        data = response.json()
        if response.status_code != 200 or data.get('code') != 200:
            return dict(result, message='ตรวจสถานะไม่สำเร็จ ลองตรวจใหม่ภายหลัง ไม่ต้องสร้างงานใหม่')
        task = data.get('data') or {}
        status = task.get('status')
        if status == 'failed':
            return dict(result, success=False, pending=False, error='Crun รายงานว่าสร้างเพลงล้มเหลว ตรวจรายละเอียดที่หน้า Logs ของ Crun')
        if status == 'success':
            body = task.get('result') or {}
            urls = body.get('media_urls') or [track.get('suno_audio_url') for track in body.get('suno_data', [])]
            urls = [url for url in urls if isinstance(url, str) and url.startswith('https://')]
            if urls:
                return dict(result, pending=False, audio_urls=urls)
            return dict(result, message='งานเสร็จแต่ยังไม่พบลิงก์เพลง ตรวจสถานะอีกครั้งหรือดูหน้า Logs ของ Crun')
        return dict(result, message='Crun กำลังสร้างเพลง รอ 15–30 วินาทีแล้วตรวจอีกครั้ง')
    except (requests.RequestException, ValueError):
        return dict(result, message='เชื่อมต่อตรวจสถานะไม่ได้ ลองใหม่ภายหลัง งานเดิมยังถูกเก็บไว้')
