"""
Kulinarcha (@kulinarcha) Telegram kanali uchun Gemini va Gibrid rasm tizimiga ega avtomat post generatori.
"""

import base64
import json
import os
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]
UNSPLASH_ACCESS_KEY = os.environ.get("PEXELS_API_KEY", "") # Ixtiyoriy real rasm uchun

GEMINI_TEXT_MODEL = "gemini-2.0-flash"
GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"

TELEGRAM_CAPTION_LIMIT = 1024
HISTORY_FILE = "history.txt"

WEEKLY_SCHEDULE = {
    0: "Nonushtalar",
    1: "Shirinliklar",
    2: "Qaylalar (birinchi, suyuq taomlar)",
    3: "Quyuq taomlar (ikkinchi taomlar)",
    4: "Ichimliklar",
    5: "Salatlar",
    6: "Maslahatlar",
}

RECIPE_TYPE_RUBRIKAS = {
    "Nonushtalar",
    "Shirinliklar",
    "Qaylalar (birinchi, suyuq taomlar)",
    "Quyuq taomlar (ikkinchi taomlar)",
    "Ichimliklar",
    "Salatlar",
}

STYLE_TEMPLATE = """\
🍗 QARSILDOQ TOVUQ

Tashqarisi qarsildoq, ichi esa shirali. Eng yaxshi tomoni — uyda bemalol tayyorlash mumkin. 😋

🛒 MASALLIQLAR:

🍗 Tovuq — 500 g
🧄 Sarimsoq — 3 dona
🧂 Tuz — 1 choy qoshiq
🌶️ Qalampir — ½ choy qoshiq
🥚 Tuxum — 1 dona
🌾 Un — 4 osh qoshiq

🔥 ASOSIY SIR:

Tovuqni ziravorlagandan keyin kamida 15 daqiqa dam oldiring. Shunda ta'mi ichigacha kiradi va go'sht quruq bo'lib qolmaydi.

👨‍🍳 TAYYORLASH:

1. Tovuqni tuz, qalampir va maydalangan sarimsoq bilan aralashtiring.
2. Tuxumga botiring.
3. Unga yaxshilab bulang.
4. Qizigan yog'da ikki tomonini tillarang bo'lguncha qovuring.
5. Tayyor bo'lgach, 5 daqiqa dam bering.

🤫 MASLAHAT:

Tovuqni yog'ga solgandan keyin darhol aylantirmang. Birinchi tomoni yaxshi qizarib olsin — shunda qobig'i qarsildoqroq chiqadi.

❤️ SAQLAB QO'YING:

Keyingi safar "nima pishirsam ekan?" deganda kerak bo'ladi.

Kulinarcha - oshxonadagi kichkina yordamchingiz. ❤️

👇 [Post mazmunidan kelib chiqib o'quvchini izoh yozishga undovchi savol]

#qarsildoqtovuq #tovuqtaom #uydaovqat #osonretsept #kulinarcha
"""

MASLAHAT_TEMPLATE = """\
🍎 [MAHSULOT YOKI MAVZU NOMI]

Qisqa, qiziqarli kirish gapi (1-2 gap), nega bu mavzu muhimligini tushuntiradi. 😋

💡 ASOSIY MA'LUMOT:

Mahsulot/mavzu haqida 2-3 ta aniq, foydali fakt (masalan tarkibi, foydasi).

🔥 QANDAY FOYDALANISH KERAK:

To'g'ri iste'mol qilish yoki qo'llash bo'yicha aniq maslahat.

🤫 MASLAHAT:

Kam odam biladigan qiziq maslahat yoki hiyla.

❤️ SAQLAB QO'YING:

Keyingi safar kerak bo'ladigan qisqa xulosa.

Kulinarcha - oshxonadagi kichkina yordamchingiz. ❤️

👇 [Post mazmunidan kelib chiqib o'quvchini izoh yozishga undovchi savol]

#sogʻlomovqatlanish #foydalimaslahat #mavzunomi #kulinarcha
"""


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def save_history(dish_name):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{dish_name}\n")


def toshkent_hafta_kuni() -> int:
    now = datetime.now(ZoneInfo("Asia/Tashkent"))
    return now.weekday()


def call_gemini(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_TEXT_MODEL}:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def matn_yoz(rubrika: str) -> dict:
    is_recipe = rubrika in RECIPE_TYPE_RUBRIKAS
    template = STYLE_TEMPLATE if is_recipe else MASLAHAT_TEMPLATE

    history = load_history()
    history_text = "\n".join(history[-60:]) if history else "Hozircha tarix bo'sh."

    vazifa = (
        f"Bugungi rubrika: \"{rubrika}\".\n\n"
        "QAT'IY QOIDALAR:\n"
        "1. Cho'chqa go'shti (pork, bacon, ham, lard) va har qanday nohalol/cho'chqa mahsulotlari ishtirok etgan "
        "taomlar, retseptlar yoki maslahatlar MUTLAQO TAQIQLANGAN! Agar shunday mahsulot tasodifan kelib qolsa, "
        "uni darhol boshqa toza va mazali halol taomga almashtiring.\n"
        "2. AVVALGI TAKRORLANISHI KERAK BO'LMAGAN TAOMLLAR/MAVZULAR (Bularni mutlaqo qayta ishlatmang!):\n"
        f"{history_text}\n\n"
        "Internetdan shu rubrikaga mos, mashhur va sinalgan bitta taom retsepti "
        "(yoki mahsulot haqida foydali ma'lumot) toping. Original matn yozing.\n\n"
        "Postni ANIQ quyidagi uslub va tuzilishda yozing (sarlavhalar, emoji va bo'limlar "
        "tartibini aynan saqlang, imzo 'Kulinarcha - oshxonadagi kichkina yordamchingiz. ❤️' va oxirgi savol joyini o'zgartirmang):\n\n"
        f"{template}\n\n"
        "QOIDALAR:\n"
        "- Faqat sof, sodda va tabiiy o'zbek tilida yozing.\n"
        "- Post umumiy uzunligi 900-1300 belgi atrofida bo'lsin.\n"
        "- YAKUNIY QATOR (👇 bilan boshlanadigan): har doim o'quvchini izohda fikr bildirishga undovchi, "
        "post mazmunidan kelib chiqadigan o'ziga xos savol bo'lsin.\n"
        "- Heshteglar 3 tadan 5 tagacha bo'lsin, oxirgisi doim #kulinarcha bo'lsin.\n\n"
        "Javobingizni ANIQ quyidagi formatda qaytaring (boshqa hech qanday izoh yozmang):\n\n"
        "@@@NOM@@@\n"
        "<taom yoki mavzu nomi>\n"
        "@@@MATN@@@\n"
        "<to'liq tayyor post matni, heshteglar bilan birga>\n"
        "@@@IMAGE_QUERY@@@\n"
        "<Unsplash yoki internetdan qidirish uchun ingliz tilidagi kalit so'z, masalan: creamy mushroom pasta>\n"
        "@@@IMAGE_PROMPT@@@\n"
        "<Gemini orqali rasm generatsiya qilish uchun ingliz tilida o'ta professional fotorealistik prompt>\n"
        "@@@TUGADI@@@"
    )

    full_text = call_gemini(vazifa)

    nom_m = re.search(r"@@@NOM@@@\s*(.*?)\s*@@@MATN@@@", full_text, re.DOTALL)
    matn_m = re.search(r"@@@MATN@@@\s*(.*?)\s*(?:@@@IMAGE_QUERY@@@|@@@TUGADI@@|$)", full_text, re.DOTALL)
    query_m = re.search(r"@@@IMAGE_QUERY@@@\s*(.*?)\s*(?:@@@IMAGE_PROMPT@@@|@@@TUGADI@@|$)", full_text, re.DOTALL)
    prompt_m = re.search(r"@@@IMAGE_PROMPT@@@\s*(.*?)\s*(?:@@@TUGADI@@$)", full_text, re.DOTALL)

    if not (nom_m and matn_m):
        raise RuntimeError(f"Gemini javobini o'qib bo'lmadi. Javob: {full_text[:1000]}")

    post_nomi = nom_m.group(1).strip()
    post_matni = matn_m.group(1).strip()
    image_query = query_m.group(1).strip() if query_m else post_nomi
    image_prompt = prompt_m.group(1).strip() if prompt_m else f"Professional food photography of {post_nomi}, appetizing, natural light"

    return {
        "post_nomi": post_nomi,
        "post_matni": post_matni,
        "image_query": image_query,
        "image_prompt": image_prompt,
    }


def find_real_image(query: str) -> bytes:
    """1-Bosqich: Unsplash API orqali real va sifatli rasm qidirish"""
    if not UNSPLASH_ACCESS_KEY:
        return None
    
    encoded_query = requests.utils.quote(query)
    url = f"https://api.unsplash.com/search/photos?query={encoded_query}&per_page=1&client_id={UNSPLASH_ACCESS_KEY}"
    
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if results:
                image_url = results[0]["urls"]["regular"]
                img_resp = requests.get(image_url, timeout=60)
                if img_resp.status_code == 200:
                    print(f"[INFO] Unsplash orqali real rasm topildi: {image_url}")
                    return img_resp.content
    except Exception as e:
        print(f"[OGOHLANTIRISH] Unsplash orqali rasm qidirishda xatolik: {e}")
    return None


def rasm_generatsiya_gemini(prompt: str) -> bytes:
    """2-Bosqich (Zaxira): Gemini API orqali rasm generatsiyasi (Imagen)"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_IMAGE_MODEL}:generateContent"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    resp = requests.post(url, params={"key": GEMINI_API_KEY}, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    
    parts = data["candidates"][0]["content"]["parts"]
    for part in parts:
        if "inlineData" in part:
            return base64.b64decode(part["inlineData"]["data"])
    raise RuntimeError("Gemini javobida rasm topilmadi.")


def rasm_media_type(rasm_bytes: bytes) -> str:
    if rasm_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    return "image/jpeg"


def telegramga_yubor(rasm_bytes: bytes, matn: str) -> None:
    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    media_type = rasm_media_type(rasm_bytes)
    fayl_nomi = "post.png" if media_type == "image/png" else "post.jpg"

    # 1. Rasmni alohida yuborish
    photo_resp = requests.post(
        f"{base_url}/sendPhoto",
        data={"chat_id": TELEGRAM_CHANNEL_ID},
        files={"photo": (fayl_nomi, rasm_bytes, media_type)},
        timeout=60
    )
    photo_resp.raise_for_status()

    # 2. Matnni alohida xabar sifatida tagiga yuborish (limit muammosini oldini oladi)
    text_resp = requests.post(
        f"{base_url}/sendMessage",
        data={"chat_id": TELEGRAM_CHANNEL_ID, "text": matn, "parse_mode": "HTML"},
        timeout=60
    )
    text_resp.raise_for_status()


def main() -> None:
    kun = toshkent_hafta_kuni()
    rubrika = WEEKLY_SCHEDULE[kun]
    print(f"[INFO] Bugungi rubrika: {rubrika}")

    natija = matn_yoz(rubrika)
    post_nomi = natija["post_nomi"]
    post_matni = natija["post_matni"]
    image_query = natija["image_query"]
    image_prompt = natija["image_prompt"]
    print(f"[INFO] Post tayyor: \"{post_nomi}\"")

    # Gibrid rasm tanlash tizimi (Smart Fallback)
    print(f"[INFO] Real rasm qidirilmoqda: {image_query}")
    rasm_bytes = find_real_image(image_query)

    if not rasm_bytes:
        print("[INFO] Real rasm topilmadi, Gemini API orqali rasm generatsiya qilinmoqda...")
        safe_prompt = f"{image_prompt}, professional food photography, 8k resolution, photorealistic, studio lighting"
        rasm_bytes = rasm_generatsiya_gemini(safe_prompt)

    print("[INFO] Rasm tayyor, Telegramga yuborilmoqda...")
    telegramga_yubor(rasm_bytes, post_matni)
    
    save_history(post_nomi)
    print("[INFO] Post muvaffaqiyatli yuborildi va tarixga yozildi.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[XATO] {exc}", file=sys.stderr)
        sys.exit(1)
