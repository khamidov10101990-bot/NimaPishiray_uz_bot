"""
Nima Pishiray — Telegram bot (2-versiya)
Butun oila uchun ovqat yordamchisi:
  - Nima pishiray: mahal (nonushta/tushlik/kechki) → oshxona → uslub (dieta/to'yimli/tez)
  - Uyda bor: mahsulotlar bo'yicha taomlar
  - Haftalik menyu: 3 mahal yoki faqat kechki + bozor ro'yxati
Taomlar dishes.json faylida. Yangi taom qo'shish uchun shu faylni tahrirlang.
"""
import asyncio
import json
import os
import random
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, KeyboardButton, Message,
                           ReplyKeyboardMarkup)

TOKEN = os.getenv("BOT_TOKEN")
HERE = Path(__file__).parent
DATA_FILE = HERE / "data.json"
DISHES = json.loads((HERE / "dishes.json").read_text(encoding="utf-8"))

MEALS = {"n": "🌅 Nonushta", "t": "☀️ Tushlik", "k": "🌙 Kechki ovqat", "d": "🍰 Shirinlik"}
CUISINES = {"all": "🌍 Farqi yo'q", "uz": "🇺🇿 O'zbek", "eu": "🍝 Yevropa",
            "as": "🥢 Osiyo", "tr": "🥙 Turk-Arab", "ru": "🥟 Rus"}
STYLES = {"all": "Farqi yo'q", "dieta": "🥗 Dieta", "toyimli": "💪 To'yimli", "tez": "⚡ Tez (30 daq)"}
STYLE_NAME = {"dieta": "dieta", "oddiy": "oddiy", "toyimli": "to'yimli"}
PANTRY = {"shakar"}  # har doim uyda bor deb hisoblanadi
ALL_ING = sorted({x for d in DISHES for x in d["i"]} - PANTRY)
DAYS = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
BY_NAME = {d["n"]: d for d in DISHES}

# ---------------- Foydalanuvchi ma'lumotlari ----------------
try:
    DB = json.loads(DATA_FILE.read_text(encoding="utf-8"))
except Exception:
    DB = {}

def user(uid: int) -> dict:
    u = DB.setdefault(str(uid), {})
    u.setdefault("recent", [])
    u.setdefault("have", ["kartoshka", "piyoz", "tuxum", "go'sht", "sabzi", "non", "sut"])
    u.setdefault("f", {"m": "k", "c": "all", "s": "all"})
    u.setdefault("week", [])
    u.setdefault("week_mode", "3")
    return u

def save():
    DATA_FILE.write_text(json.dumps(DB, ensure_ascii=False, indent=1), encoding="utf-8")

# ---------------- Klaviaturalar ----------------
BTN_TODAY, BTN_FRIDGE, BTN_WEEK = "🍽 Nima pishiray?", "🧊 Uyda nima bor?", "📅 Haftalik menyu"
MAIN_KB = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=BTN_TODAY)], [KeyboardButton(text=BTN_FRIDGE), KeyboardButton(text=BTN_WEEK)]],
    resize_keyboard=True,
)

def ib(text, data):
    return InlineKeyboardButton(text=text, callback_data=data)

def grid(buttons, per_row):
    return [buttons[i:i + per_row] for i in range(0, len(buttons), per_row)]

def meal_kb():
    return InlineKeyboardMarkup(inline_keyboard=grid([ib(v, f"m:{k}") for k, v in MEALS.items()], 2))

def cuisine_kb():
    return InlineKeyboardMarkup(inline_keyboard=grid([ib(v, f"c:{k}") for k, v in CUISINES.items()], 2))

def style_kb():
    return InlineKeyboardMarkup(inline_keyboard=grid([ib(v, f"s:{k}") for k, v in STYLES.items()], 2))

def fridge_kb(have):
    btns = [ib(("✅ " if x in have else "") + x, f"ing:{i}") for i, x in enumerate(ALL_ING)]
    rows = grid(btns, 3)
    rows.append([ib("🔎 Nima pishirsa bo'ladi?", "fridge:go")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def week_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [ib("🔄 Yangi hafta (3 mahal)", "week:3")],
        [ib("🔄 Faqat kechki ovqat", "week:1")],
    ])

# ---------------- Yordamchi ----------------
def fmt_time(t):
    return f"{t} daq" if t < 60 else f"{t / 60:.1f}".replace(".0", "").replace(".", ",") + " soat"

def dish_text(d, have):
    ings = ", ".join(("✅" if x in have or x in PANTRY else "▫️") + x for x in d["i"])
    return (f"🍽 <b>{d['n']}</b>\n"
            f"⏱ {fmt_time(d['t'])} · {CUISINES[d['c']]} · {STYLE_NAME[d['s']]} · ~{d['kcal']} kkal\n\n"
            f"{d['d']}\n\n<i>Mahsulotlar:</i> {ings}")

def filter_dishes(f):
    out = []
    for d in DISHES:
        if f["m"] not in d["m"]:
            continue
        if f["c"] != "all" and d["c"] != f["c"]:
            continue
        if f["s"] == "tez" and d["t"] > 30:
            continue
        if f["s"] in ("dieta", "toyimli") and d["s"] != f["s"]:
            continue
        out.append(d)
    return out

def filter_label(f):
    return f"{MEALS[f['m']]} · {CUISINES[f['c']]} · {STYLES[f['s']]}"

def make_week(mode):
    used, week = set(), []
    for i in range(7):
        weekend = i >= 5
        day = {}
        for m in (["n", "t", "k"] if mode == "3" else ["k"]):
            limit = 999 if weekend else (20 if m == "n" else 70)
            pool = [d for d in DISHES if m in d["m"] and d["t"] <= limit and d["n"] not in used]
            pool = pool or [d for d in DISHES if m in d["m"]]
            d = random.choice(pool)
            used.add(d["n"])
            day[m] = d["n"]
        week.append(day)
    return week

def week_text(u):
    lines = ["📅 <b>Haftalik menyu</b>"]
    need = {}
    for dayname, day in zip(DAYS, u["week"]):
        lines.append(f"\n<b>{dayname}</b>")
        for m in ("n", "t", "k"):
            if m in day and day[m] in BY_NAME:
                d = BY_NAME[day[m]]
                lines.append(f"{MEALS[m].split()[0]} {d['n']}")
                for x in d["i"]:
                    if x not in u["have"] and x not in PANTRY:
                        need[x] = need.get(x, 0) + 1
    lines.append("\n🛒 <b>Bozor ro'yxati</b> (uyda yo'qlari)")
    if need:
        lines += [f"• {x}" + (f" ×{c}" if c > 1 else "") for x, c in sorted(need.items(), key=lambda kv: -kv[1])]
    else:
        lines.append("Uyda hammasi bor ekan 👍")
    return "\n".join(lines)

# ---------------- Handlerlar ----------------
dp = Dispatcher()

@dp.message(CommandStart())
async def start(m: Message):
    user(m.from_user.id); save()
    await m.answer(
        "Assalomu alaykum! Men <b>Nima Pishiray</b> botiman 🍲\n\n"
        "Nonushta, tushlik, kechki ovqat yoki shirinlik uchun bosh qotirmang. "
        "O'zbek, Yevropa, Osiyo taomlari, dieta yoki to'yimli, hammasi bor.\n\n"
        "Pastdagi tugmani bosing 👇",
        reply_markup=MAIN_KB,
    )

# --- Nima pishiray: mahal → oshxona → uslub ---
@dp.message(F.text == BTN_TODAY)
async def today(m: Message):
    await m.answer("Qaysi mahal uchun?", reply_markup=meal_kb())

@dp.callback_query(F.data.startswith("m:"))
async def set_meal(c: CallbackQuery):
    u = user(c.from_user.id); u["f"]["m"] = c.data[2:]; save()
    await c.message.edit_text(f"{MEALS[u['f']['m']]}\n\nQaysi oshxona?", reply_markup=cuisine_kb())
    await c.answer()

@dp.callback_query(F.data.startswith("c:"))
async def set_cuisine(c: CallbackQuery):
    u = user(c.from_user.id); u["f"]["c"] = c.data[2:]; save()
    await c.message.edit_text(f"{MEALS[u['f']['m']]} · {CUISINES[u['f']['c']]}\n\nQanaqasi bo'lsin?", reply_markup=style_kb())
    await c.answer()

@dp.callback_query(F.data.startswith("s:"))
async def set_style(c: CallbackQuery):
    u = user(c.from_user.id); u["f"]["s"] = c.data[2:]; save()
    await suggest(c)

@dp.callback_query(F.data == "again")
async def again(c: CallbackQuery):
    await suggest(c)

async def suggest(c: CallbackQuery):
    u = user(c.from_user.id)
    pool = filter_dishes(u["f"])
    if not pool:
        await c.message.edit_text(
            f"{filter_label(u['f'])}\n\nBu shartlarga mos taom topilmadi 😕 Boshqa oshxona yoki uslubni tanlab ko'ring.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[ib("⚙️ Qaytadan tanlash", "restart")]]))
        await c.answer(); return
    fresh = [d for d in pool if d["n"] not in u["recent"]] or pool
    d = random.choice(fresh)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [ib("🔄 Boshqasi", "again"), ib("👍 Shu bo'lsin!", f"ok:{DISHES.index(d)}")],
        [ib("⚙️ Qaytadan tanlash", "restart")],
    ])
    await c.message.edit_text(f"<i>{filter_label(u['f'])} · {len(pool)} ta variant</i>\n\n" + dish_text(d, u["have"]), reply_markup=kb)
    await c.answer()

@dp.callback_query(F.data == "restart")
async def restart(c: CallbackQuery):
    await c.message.edit_text("Qaysi mahal uchun?", reply_markup=meal_kb())
    await c.answer()

@dp.callback_query(F.data.startswith("ok:"))
async def chosen(c: CallbackQuery):
    u = user(c.from_user.id)
    d = DISHES[int(c.data[3:])]
    u["recent"] = ([d["n"]] + [x for x in u["recent"] if x != d["n"]])[:10]; save()
    await c.message.edit_text(dish_text(d, u["have"]) + "\n\n✅ <b>Tanlandi. Yoqimli ishtaha!</b>")
    await c.answer("Tanlandi!")

# --- Uyda bor ---
@dp.message(F.text == BTN_FRIDGE)
async def fridge(m: Message):
    await m.answer("Uyda bor mahsulotlarni belgilang:", reply_markup=fridge_kb(user(m.from_user.id)["have"]))

@dp.callback_query(F.data.startswith("ing:"))
async def toggle_ing(c: CallbackQuery):
    u = user(c.from_user.id)
    ing = ALL_ING[int(c.data[4:])]
    u["have"] = [x for x in u["have"] if x != ing] if ing in u["have"] else u["have"] + [ing]
    save()
    await c.message.edit_reply_markup(reply_markup=fridge_kb(u["have"]))
    await c.answer()

@dp.callback_query(F.data == "fridge:go")
async def fridge_go(c: CallbackQuery):
    have = set(user(c.from_user.id)["have"]) | PANTRY
    ranked = []
    for d in DISHES:
        h = sum(x in have for x in d["i"])
        if h:
            ranked.append((len(d["i"]) - h, -h, d))
    ranked.sort(key=lambda r: (r[0], r[1]))
    if not ranked:
        await c.answer("Kamida bitta mahsulot belgilang", show_alert=True); return
    lines = ["🧊 <b>Uydagi narsalardan:</b>\n"]
    for _, _, d in ranked[:10]:
        need = [x for x in d["i"] if x not in have]
        meals = "".join(MEALS[m].split()[0] for m in d["m"])
        lines.append(f"{meals} <b>{d['n']}</b> — " + ("hammasi bor ✅" if not need else "kerak: " + ", ".join(need)))
    await c.message.answer("\n".join(lines))
    await c.answer()

# --- Haftalik ---
@dp.message(F.text == BTN_WEEK)
async def week(m: Message):
    u = user(m.from_user.id)
    if len(u["week"]) != 7 or not isinstance(u["week"][0], dict):
        u["week"] = make_week(u["week_mode"]); save()
    await m.answer(week_text(u), reply_markup=week_kb())

@dp.callback_query(F.data.startswith("week:"))
async def week_new(c: CallbackQuery):
    u = user(c.from_user.id)
    u["week_mode"] = c.data[5:]
    u["week"] = make_week(u["week_mode"]); save()
    await c.message.edit_text(week_text(u), reply_markup=week_kb())
    await c.answer("Yangi menyu tayyor")

# ---------------- Ishga tushirish ----------------
async def keep_alive_server():
    """Render kabi bepul hostinglar uchun: PORT berilgan bo'lsa, kichik veb-sahifa ochadi.
    UptimeRobot shu sahifani har 5 daqiqada ochib turadi, shunda server uxlab qolmaydi."""
    port = os.getenv("PORT")
    if not port:
        return
    from aiohttp import web
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="Nima Pishiray bot ishlayapti ✅"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(port)).start()
    print(f"Veb-sahifa {port}-portda ochildi")


async def main():
    if not TOKEN:
        raise SystemExit("BOT_TOKEN topilmadi. README.md ni ko'ring.")
    await keep_alive_server()
    bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot ishga tushdi ✅")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
