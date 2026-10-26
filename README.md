# Nima Pishiray — Telegram bot

## 1. Bot yaratish (2 daqiqa)
1. Telegramda **@BotFather** ni oching.
2. `/newbot` yozing, nom bering (masalan: *Nima Pishiray*), keyin username (masalan: `nima_pishiray_bot`).
3. BotFather sizga **token** beradi (`123456:ABC...` ko'rinishida). Uni hech kimga bermang.

## 2. Kompyuterda ishga tushirish (sinash uchun)
Python 3.10+ kerak.

```bash
pip install -r requirements.txt

# Windows (PowerShell):
$env:BOT_TOKEN="SIZNING_TOKEN"
python bot.py

# Mac / Linux:
BOT_TOKEN="SIZNING_TOKEN" python bot.py
```

"Bot ishga tushdi ✅" chiqsa, Telegramda botingizga `/start` yozing.
Kompyuter o'chsa, bot ham to'xtaydi.

## 3. Doimiy ishlashi uchun (server)
Bot 24/7 ishlashi uchun uni serverga qo'yish kerak. Arzon variantlar:
- **Railway** yoki **Render** — GitHub'ga yuklab, bir necha bosishda ishga tushadi.
- **VPS** (oyiga bir necha dollar) — `python bot.py` ni doimiy ishlatib qo'yasiz.

Har ikkalasida `BOT_TOKEN` ni "Environment variables" bo'limiga yozasiz.

## O'zgartirish
- Yangi taom qo'shish: `dishes.json` fayliga xuddi shu ko'rinishda qator qo'shing.
  `m`: n=nonushta, t=tushlik, k=kechki · `c`: uz/eu/as/tr/ru · `s`: dieta/oddiy/toyimli
- Foydalanuvchi ma'lumotlari `data.json` faylida saqlanadi.

## 2-versiyada nima yangi
- Nonushta, tushlik, kechki ovqat
- Oshxonalar: O'zbek, Yevropa, Osiyo, Turk-Arab, Rus
- Uslub: dieta, to'yimli, tez (30 daqiqagacha), taxminiy kaloriya
- Haftalik menyu: 3 mahal yoki faqat kechki
- Taomlar endi `dishes.json` faylida. GitHub'ga shu faylni ham yuklang.
