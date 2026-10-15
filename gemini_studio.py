"""Gemini REST chat with structured song fields. No keys are persisted."""
import json
import requests
from producer_rules import RULES, normalize, format_package

MODEL = 'gemini-3.5-flash-lite'
FIELDS = ('turn_type', 'reply', 'title', 'style', 'description', 'lyrics', 'tags', 'ai_prompts', 'image_prompt')

def chat(key, messages, channel, song):
    if not key.strip():
        return {'success': False, 'error': 'กรุณาใส่ Gemini API Key ในแถบซ้ายแล้วกด Enter'}
    schema = {'type': 'OBJECT', 'properties': {field: {'type': 'STRING'} for field in FIELDS}, 'required': list(FIELDS)}
    instruction = RULES + '''
ข้อกำหนดการสนทนาซึ่งมีลำดับเหนือกฎรูปแบบข้างต้น: ตอบโต้และช่วยคิดเป็นภาษาไทยตามปกติก่อน ห้ามแต่งหรือแก้แพ็กเพลงเองจากข้อความบรีฟ คำถาม หรือคำยืนยันทั่วไป เช่น โอเค ให้ turn_type=chat และ reply เป็นคำตอบสนทนาที่มีสาระ ช่องเพลงทั้งหมดเป็นสตริงว่าง กฎหกกล่องใช้เฉพาะเมื่อผู้ใช้สั่งแต่งเพลงหรือแก้ร่างอย่างชัดเจน ให้ turn_type=draft และส่งครบทุกช่องเป็นร่างให้ตรวจ ผู้ใช้ต้องกดปุ่มยืนยันในแอปเองจึงจะนำร่างลงช่องแก้ไข ห้ามอ้างว่าได้ใส่หรือสร้างเสียงแล้ว หากขอความยาว 4 นาทีต้องวางจำนวนบาร์อย่างน้อย 240 วินาทีตาม BPM มีเนื้อร้องเต็มหลายท่อน ไม่ใช่สี่บรรทัดและป้ายเวลาลอยๆ รักษาบรีฟและข้อแก้ไขจากบทสนทนา เมื่อขอเลือกคีย์เวิร์ดให้เสนอรายการใน reply แล้วรอผู้ใช้เลือก ไม่สร้างแพ็กเอง
''' + f'\nช่องเป้าหมาย: {channel}\nเพลงปัจจุบัน: {json.dumps(song, ensure_ascii=False)}'
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
        if result['turn_type'] not in ('chat', 'draft'):
            raise ValueError('Invalid turn type')
        if result['turn_type'] == 'draft':
            if not all(result[field].strip() for field in ('title', 'style', 'lyrics')):
                raise ValueError('Incomplete draft')
            result = normalize(result, channel)
            result['reply'] = format_package(result)
        return {'success':True, **result}
    except requests.Timeout:
        return {'success':False,'error':'Gemini ตอบช้าเกิน 60 วินาที กรุณาลองส่งข้อความใหม่'}
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return {'success':False,'error':'ยังไม่ได้คำตอบที่สมบูรณ์จาก Gemini กรุณาลองใหม่'}

