import uvicorn
import json
import os
import re
from fastapi import FastAPI
from fastapi.responses import HTMLResponse # <--- HTML qaytarish uchun kerak
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

# API Kalit (OpenRouter)
api_key = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class SimulationRequest(BaseModel):
    bot_code: str
    chat_history: list

# --- ASOSIY O'ZGARISH SHU YERDA ---
# Brauzerda saytni ochganda index.html faylini yuklaymiz
@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Xatolik! index.html fayli topilmadi.</h1>"
# ----------------------------------

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
            "4. MUHIM: Javobing faqat JSON bo'lsin, markdown ishlatma."
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "system", "content": f"BOT KODI:\n{request.bot_code}"}
        ]
        
        for m in request.chat_history:
            role = "user" if m['sender'] == 'user' else "assistant"
            messages.append({"role": role, "content": m['text']})

        response = client.chat.completions.create(
            model="google/gemini-3-flash-preview", # Yoki: google/gemini-2.0-flash-lite-preview-02-05:free
            messages=messages,
            temperature=0
        )

        content = response.choices[0].message.content
        
        # DeepSeek va boshqa modellardan kelgan javobni tozalash
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.replace("```", "").strip()

        return json.loads(content)

    except Exception as e:
        return {"text": f"❌ Tizim xatosi: {str(e)}", "buttons": []}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # Ekranda 127.0.0.1:8000 manzilini ochishingiz mumkin
    uvicorn.run(app, host="0.0.0.0", port=port)


