import base64
import requests

def generate(key, prompt):
    if not key.strip():
        return {"error": "กรอก OpenAI API Key สำหรับสร้างภาพก่อน"}
    if not prompt.strip():
        return {"error": "กรอก Image Prompt ก่อนสร้างภาพ"}
    try:
        response = requests.post("https://api.openai.com/v1/images/generations",
            headers={"Authorization": "Bearer " + key.strip()},
            json={"model": "gpt-image-2.5-sunburst", "prompt": prompt,
                  "size": "1536x1024", "quality": "low", "n": 1}, timeout=180)
        if response.status_code != 200:
            messages = {401: "คีย์ OpenAI ไม่ถูกต้อง", 403: "บัญชียังไม่มีสิทธิ์ใช้โมเดลภาพ",
                        429: "โควตาหรือเครดิต OpenAI ไม่พอ หรือเรียกถี่เกินไป"}
            return {"error": messages.get(response.status_code, "สร้างภาพไม่สำเร็จ กรุณาตรวจบัญชี OpenAI")}
        data = base64.b64decode(response.json()["data"][0]["b64_json"], validate=True)
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            return {"error": "ผลลัพธ์ไม่ใช่ไฟล์ PNG ที่ถูกต้อง"}
        return {"image": data}
    except requests.Timeout:
        return {"error": "หมดเวลารอภาพ ยังไม่ทราบผล กรุณาตรวจรายการใช้งานก่อนกดซ้ำ"}
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return {"error": "รับผลสร้างภาพไม่สำเร็จ"}
