"""Gemini REST chat with structured song fields. No keys are persisted."""
import json
import requests

MODEL = 'gemini-2.5-flash-lite'
FIELDS = ('reply', 'title', 'style', 'lyrics', 'image_prompt')

def chat(key, messages, channel, song):
    if not key.strip():
        return {'success': False, 'error': 'กรุณาใส่ Gemini API Key ในแถบซ้ายแล้วกด Enter'}
    schema = {'type': 'OBJECT', 'properties': {field: {'type': 'STRING'} for field in FIELDS}, 'required': list(FIELDS)}
    instruction = ('คุณเป็นผู้ช่วยแต่งเพลงภาษาไทย คุยตามคำขอและประวัติสนทนา แต่งเนื้อใหม่ไม่คัดลอกเพลงเดิม '
                   'ตอบ reply เป็นภาษาไทย ช่อง title/style/lyrics/image_prompt เป็นเพลงฉบับล่าสุด '
                   'หากแค่ถามทั่วไปให้คงข้อมูลเพลงเดิม ไม่รับประกันการผ่านนโยบาย YouTube '
                   'style และ image_prompt ใช้ภาษาอังกฤษ เนื้อเพลงใช้ภาษาไทยเว้นแต่ผู้ใช้ระบุภาษาอื่น '
                   'อย่าอ้างว่าได้สร้างเสียงเพลงแล้ว การแชทนี้สร้างข้อความเท่านั้น '
                   f'ช่องเป้าหมาย: {channel}\nเพลงปัจจุบัน: {json.dumps(song, ensure_ascii=False)}')
    contents = [{'role': 'user' if msg['role']=='user' else 'model', 'parts':[{'text':msg['content']}]} for msg in messages[-16:]]
    while contents and contents[0]['role'] != 'user':
        contents.pop(0)
    try:
        response = requests.post(f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent',
            headers={'x-goog-api-key':key.strip(), 'Content-Type':'application/json'}, timeout=60,
            json={'systemInstruction': {'parts':[{'text':instruction}]}, 'contents':contents,
                  'generationConfig':{'responseMimeType':'application/json','responseSchema':schema,'maxOutputTokens':8192}})
        if response.status_code != 200:
            errors = {400:'คีย์หรือคำขอไม่ถูกต้อง',403:'คีย์ไม่มีสิทธิ์เรียก Gemini',404:'ไม่พบโมเดล Gemini ที่กำหนด',429:'โควตา Gemini หมดหรือติดจำกัดการเรียก ลองใหม่ภายหลัง',503:'Gemini ไม่พร้อมใช้งานชั่วคราว'}
            return {'success':False,'error':f'Gemini HTTP {response.status_code}: '+errors.get(response.status_code,'เรียกบริการไม่สำเร็จ')}
        data = response.json()
        parts = (data.get('candidates') or [{}])[0].get('content',{}).get('parts',[])
        text = ''.join(part.get('text','') for part in parts if not part.get('thought'))
        result = json.loads(text)
        if not all(isinstance(result.get(field),str) for field in FIELDS):
            raise ValueError('Invalid song schema')
        return {'success':True, **result}
    except requests.Timeout:
        return {'success':False,'error':'Gemini ตอบช้าเกิน 60 วินาที กรุณาลองส่งข้อความใหม่'}
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return {'success':False,'error':'ยังไม่ได้คำตอบที่สมบูรณ์จาก Gemini กรุณาลองใหม่'}
