import uvicorn
import json
import os  # Tizim o'zgaruvchilari bilan ishlash uchun
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

# 1. Xavfsiz usul: API kalitni Environment Variable orqali olamiz
# Render sozlamalarida OPENAI_API_KEY nomli o'zgaruvchi yaratishingiz kerak
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

app = FastAPI()

# CORS sozlamalari (Frontend ulanishi uchun)
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

class SimulationRequest(BaseModel):
    bot_code: str
    chat_history: list

# 2. Root yo'nalishi: Brauzerda kirganda "Not Found" chiqmasligi uchun
@app.get("/")
async def read_root():
    return {"status": "active", "message": "AI Bot Simulator API ishlamoqda!"}

@app.post("/simulate")
async def simulate_bot(request: SimulationRequest):
    try:
        system_instruction = (
            "Sen qat'iy va aqlli Telegram bot simulyatorisan. Vazifang foydalanuvchi yuborgan Python kodini "
            "tahlil qilish va virtual chatda unga muvofiq javob qaytarish."
            "\n\nQOIDALAR:\n"
            "1. KODNI TEKSHIRISH: Agar Python kodida xato bo'lsa, 'text' maydonida FAQAT xato haqida xabar ber.\n"
            "2. TUGMALAR: markup.add() orqali qo'shilgan tugmalarni 'buttons' massiviga chiqar.\n"
            "3. JAVOB FORMATI: Doimo JSON qaytar: {'text': '...', 'buttons': [...]}\n"
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "system", "content": f"BOT KODI:\n{request.bot_code}"}
        ]
        
        for m in request.chat_history:
            role = "user" if m['sender'] == 'user' else "assistant"
            messages.append({"role": role, "content": m['text']})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={ "type": "json_object" },
            temperature=0 
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        return {"text": f"❌ Simulyatsiya xatosi: {str(e)}", "buttons": []}

# 3. Render uchun PORT va HOST sozlamalari
if __name__ == "__main__":
    # Render o'zi beradigan portni olamiz, bo'lmasa 8000
    port = int(os.environ.get("PORT", 8000))
    # Host 0.0.0.0 bo'lishi shart, aks holda server tashqariga chiqmaydi
    uvicorn.run(app, host="0.0.0.0", port=port)
