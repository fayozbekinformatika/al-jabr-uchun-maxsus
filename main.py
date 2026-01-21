import uvicorn
import json
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

# API kalitni o'chirib, o'zingizning yangi kalitingizni qo'ying
client = OpenAI(api_key="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")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class SimulationRequest(BaseModel):
    bot_code: str
    chat_history: list

@app.post("/simulate")
async def simulate_bot(request: SimulationRequest):
    try:
        system_instruction = (
            "Sen qat'iy va aqlli Telegram bot simulyatorisan. Vazifang foydalanuvchi yuborgan Python kodini "
            "tahlil qilish va virtual chatda unga muvofiq javob qaytarish."
            "\n\nQOIDALAR:\n"
            "1. KODNI TEKSHIRISH: Agar Python kodida sintaktik xato (masalan: qavslar, ikki nuqta, noto'g'ri indentatsiya) "
            "yoki mantiqiy xato (aniqlanmagan funksiya yoki o'zgaruvchi) bo'lsa, 'text' maydonida FAQAT xato haqida xabar ber. "
            "Kodni o'zingdan to'g'irlama!\n"
            "2. TUGMALAR: Kodda types.ReplyKeyboardMarkup yoki types.InlineKeyboardMarkup ichida markup.add() orqali "
            "qo'shilgan barcha tugmalarni 'buttons' massiviga chiqar.\n"
            "3. JAVOB FORMATI: Doimo JSON qaytar:\n"
            "{\n"
            "  'text': 'Bot javobi yoki xato xabari',\n"
            "  'buttons': ['tugma1', 'tugma2']\n"
            "}\n"
            "4. KONTEKST: Chat tarixiga qarab bot hozir qaysi holatda ekanini aniqlang."
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "system", "content": f"BOT KODI:\n{request.bot_code}"}
        ]
        
        for m in request.chat_history:
            role = "user" if m['sender'] == 'user' else "assistant"
            messages.append({"role": role, "content": m['text']})

        # Temperature=0 xatolarni aniq ko'rsatish uchun muhim
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={ "type": "json_object" },
            temperature=0 
        )

        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        return {"text": f"❌ Simulyatsiya xatosi: {str(e)}", "buttons": []}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)