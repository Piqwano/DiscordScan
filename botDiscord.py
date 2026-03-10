import discord
from discord import app_commands
from datetime import datetime, timezone, timedelta
import asyncio
import os
import urllib.request
import urllib.parse
import json

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Weather: Open-Meteo — completely free, no API key needed
# Currency: ExchangeRate-API open access — completely free, no API key needed
TOKYO_LAT,  TOKYO_LON  = 35.6762, 139.6503
KYOTO_LAT,  KYOTO_LON  = 35.0116, 135.7681
OSAKA_LAT,  OSAKA_LON  = 34.6937, 135.5023

JAPAN_DEPARTURE = datetime(2026, 5, 25, 10, 0, 0, tzinfo=timezone.utc)
JAPAN_RETURN    = datetime(2026, 6, 12, 0, 0, 0, tzinfo=timezone.utc)
TRIP_DAYS       = 18

# Melbourne midnight is calculated dynamically to handle AEDT/AEST automatically
GENERAL_CHANNEL_NAME   = "general"

JAPAN_FACTS = [
    "Japan has more than 6,800 islands, but most people live on just four of them.",
    "Vending machines in Japan outnumber convenience stores — there's roughly one for every 23 people.",
    "Japan has the world's oldest continuously operating company, Kongō Gumi, a construction firm founded in 578 AD.",
    "The Japanese train network is so punctual that delays of even one minute are officially recorded.",
    "Japan has over 1,500 earthquakes every year — most are too small to feel.",
    "There are more 7-Elevens in Japan than in the United States.",
    "Japanese convenience store food is so good it's considered a legitimate cuisine.",
    "Japan has a forest therapy practice called Shinrin-yoku (forest bathing) that doctors actually prescribe.",
    "The Japanese postal service once delivered mail by submarine to remote islands.",
    "Japan consumes more than half of the world's wasabi — and most of it is fake horseradish.",
    "Kit Kat has over 300 flavours in Japan including sake, matcha, and sweet potato.",
    "Japan's literacy rate is close to 100%, one of the highest in the world.",
    "The Shinkansen bullet train has a 50+ year safety record with zero passenger fatalities.",
    "Japan has more Michelin-starred restaurants than any other country in the world.",
    "Napping at work (inemuri) is considered a sign of hard work in Japan.",
    "Japanese convenience stores sell everything from fresh sushi to insurance policies.",
    "The word 'emoji' comes from Japanese: e (picture) + moji (character).",
    "Japan has a rabbit island, a cat island, a fox village, and a deer park — all real places.",
    "Sumo is Japan's national sport and wrestlers follow strict rules even outside the ring.",
    "Japanese people have one of the longest average lifespans in the world.",
]

# ─────────────────────────────────────────
intents = discord.Intents.default()
client  = discord.Client(intents=intents)
tree    = app_commands.CommandTree(client)


# ── Helpers ─────────────────────────────

def fetch_json(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return json.loads(r.read().decode())
    except Exception:
        return {}


def build_countdown_embed() -> discord.Embed:
    now   = datetime.now(timezone.utc)
    delta = JAPAN_DEPARTURE - now

    if delta.total_seconds() < 0:
        return_delta = JAPAN_RETURN - now
        if return_delta.total_seconds() > 0:
            d = return_delta.days
            h, rem = divmod(int(return_delta.total_seconds()) % 86400, 3600)
            m, s   = divmod(rem, 60)
            embed = discord.Embed(
                title="🇯🇵 Rob is in Japan RIGHT NOW!",
                description="The trip is underway — enjoy every second! 🎌",
                color=0xE60026,
            )
            embed.add_field(name="⏳ Time left in Japan", value=f"`{d}d {h}h {m}m {s}s`", inline=False)
            embed.add_field(name="✈️ Return flight",      value="QF80 → Melbourne",        inline=True)
            embed.add_field(name="🗓️ Trip length",        value=f"{TRIP_DAYS} days",        inline=True)
            embed.set_footer(text="Ganbatte! 🇯🇵")
            return embed
        else:
            embed = discord.Embed(
                title="🏠 Rob is back from Japan",
                description="Trip complete. Start planning the next one.",
                color=0x7289DA,
            )
            embed.set_footer(text="Sayonara, Japan 👋")
            return embed

    total_seconds  = int(delta.total_seconds())
    days           = delta.days
    hours, rem     = divmod(total_seconds % 86400, 3600)
    minutes, secs  = divmod(rem, 60)
    weeks          = days // 7
    remaining_days = days % 7
    months         = days // 30

    trip_announced = datetime(2025, 11, 1, tzinfo=timezone.utc)
    total_wait     = (JAPAN_DEPARTURE - trip_announced).total_seconds()
    elapsed        = (now - trip_announced).total_seconds()
    progress_pct   = max(0, min(100, int((elapsed / total_wait) * 100)))
    bar_filled     = progress_pct // 5
    bar            = "█" * bar_filled + "░" * (20 - bar_filled)

    embed = discord.Embed(
        title="✈️ Japan Countdown — Rob's Big Trip",
        description=(
            f"**QF79 Melbourne → Tokyo** departs **25 May 2026**\n"
            f"Returning **12 June 2026** on QF80 · {TRIP_DAYS} days on the ground 🇯🇵"
        ),
        color=0xE60026,
    )
    embed.add_field(name="⏳ Time Remaining", value=f"```{days}d  {hours}h  {minutes}m  {secs}s```", inline=False)
    embed.add_field(name="📅 Days",   value=f"`{days}`",                 inline=True)
    embed.add_field(name="📆 Weeks",  value=f"`{weeks}w {remaining_days}d`", inline=True)
    embed.add_field(name="🗓️ Months", value=f"`~{months} months`",       inline=True)
    embed.add_field(name=f"🚀 Trip Progress  {progress_pct}%", value=f"`{bar}`", inline=False)
    embed.add_field(name="🛫 Outbound", value="QF79 Melbourne → Tokyo", inline=True)
    embed.add_field(name="🛬 Return",   value="QF80 Tokyo → Melbourne", inline=True)
    embed.set_footer(text=f"Last updated: {now.strftime('%d %b %Y %H:%M UTC')} · Ganbatte Rob! 🇯🇵")
    return embed


# ── Slash commands ───────────────────────

@tree.command(name="ping", description="Check the bot is alive (also earns you the Active Developer badge!)")
async def ping(interaction: discord.Interaction):
    latency = round(client.latency * 1000)
    await interaction.response.send_message(
        f"🏓 Pong! Latency: **{latency}ms**\n"
        f"-# Use this command once, wait 24h, then claim your badge at discord.com/developers/active-developer",
        ephemeral=True,
    )


@tree.command(name="japan", description="How long until Rob leaves for Japan? 🇯🇵")
async def japan(interaction: discord.Interaction):
    await interaction.response.send_message(embed=build_countdown_embed())


@tree.command(name="trip", description="Full trip details — flights & upgrades")
async def trip(interaction: discord.Interaction):
    embed = discord.Embed(title="🗾 Rob's Japan Trip 2026 — Full Details", color=0xE60026)
    embed.add_field(name="📅 Dates",      value="25 May → 12 June 2026 (18 days)",                       inline=False)
    embed.add_field(name="✈️ Outbound",   value="QF79 Melbourne → Tokyo", inline=True)
    embed.add_field(name="✈️ Return",     value="QF80 Tokyo → Melbourne", inline=True)
    embed.add_field(name="🏔️ Activities", value="Exploring · Food · Culture · Travel",                    inline=True)
    embed.set_footer(text="Japan 2026 🇯🇵")
    await interaction.response.send_message(embed=embed)


@tree.command(name="weather", description="Current weather in Tokyo, Kyoto & Osaka 🌤️")
async def weather(interaction: discord.Interaction):
    await interaction.response.defer()

    cities = [
        ("Tokyo", TOKYO_LAT, TOKYO_LON),
        ("Kyoto", KYOTO_LAT, KYOTO_LON),
        ("Osaka", OSAKA_LAT, OSAKA_LON),
    ]
    embed = discord.Embed(title="🌤️ Japan Weather", color=0xE60026)

    wmo_emojis = {
        0: "☀️ Clear", 1: "🌤️ Mainly clear", 2: "⛅ Partly cloudy", 3: "☁️ Overcast",
        45: "🌫️ Foggy", 48: "🌫️ Icy fog", 51: "🌦️ Light drizzle", 53: "🌦️ Drizzle",
        55: "🌧️ Heavy drizzle", 61: "🌧️ Light rain", 63: "🌧️ Rain", 65: "🌧️ Heavy rain",
        71: "❄️ Light snow", 73: "❄️ Snow", 75: "❄️ Heavy snow", 80: "🌦️ Showers",
        81: "🌧️ Heavy showers", 95: "⛈️ Thunderstorm",
    }

    for name, lat, lon in cities:
        url  = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,apparent_temperature,relative_humidity_2m,weather_code"
            f"&timezone=Asia/Tokyo"
        )
        data = fetch_json(url)
        cur  = data.get("current", {})
        if cur:
            temp   = round(cur.get("temperature_2m", 0))
            feels  = round(cur.get("apparent_temperature", 0))
            humid  = cur.get("relative_humidity_2m", "?")
            code   = cur.get("weather_code", 0)
            desc   = wmo_emojis.get(code, "🌡️ Unknown")
            embed.add_field(
                name=f"{name}",
                value=f"**{temp}°C** (feels {feels}°C)\n{desc}\nHumidity: {humid}%",
                inline=True,
            )
        else:
            embed.add_field(name=name, value="Unavailable", inline=True)

    embed.set_footer(text=f"Updated: {datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')} · Powered by Open-Meteo")
    await interaction.followup.send(embed=embed)


@tree.command(name="yen", description="Live GBP & AUD to JPY exchange rates 💴")
async def yen(interaction: discord.Interaction):
    await interaction.response.defer()

    embed = discord.Embed(title="💴 Currency → Japanese Yen", color=0xE60026)

    for code, flag in [("GBP", "🇬🇧"), ("AUD", "🇦🇺")]:
        url  = f"https://open.er-api.com/v6/latest/{code}"
        data = fetch_json(url)
        rate = data.get("rates", {}).get("JPY")
        if rate:
            value = (
                f"**1 {code} = ¥{rate:,.2f}**\n"
                f"50 {code} = ¥{rate*50:,.0f}\n"
                f"100 {code} = ¥{rate*100:,.0f}\n"
                f"500 {code} = ¥{rate*500:,.0f}\n"
                f"1,000 {code} = ¥{rate*1000:,.0f}"
            ) if code == "GBP" else (
                f"**1 {code} = ¥{rate:,.2f}**\n"
                f"100 {code} = ¥{rate*100:,.0f}\n"
                f"500 {code} = ¥{rate*500:,.0f}\n"
                f"1,000 {code} = ¥{rate*1000:,.0f}"
            )
            embed.add_field(name=f"{flag} {code} → JPY", value=value, inline=True)

    embed.set_footer(text=f"Updated: {datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')} · Powered by ExchangeRate-API")
    await interaction.followup.send(embed=embed)


@tree.command(name="fact", description="Random Japan fact 🎌")
async def fact(interaction: discord.Interaction):
    import random
    chosen = random.choice(JAPAN_FACTS)
    embed  = discord.Embed(title="🎌 Japan Fact", description=chosen, color=0xE60026)
    embed.set_footer(text="Use /fact again for another one!")
    await interaction.response.send_message(embed=embed)


@tree.command(name="phrase", description="Random useful Japanese phrase with pronunciation 🗣️")
async def phrase(interaction: discord.Interaction):
    import random
    phrases = [
        ("ありがとうございます", "Arigatou gozaimasu", "Thank you very much"),
        ("すみません", "Sumimasen", "Excuse me / Sorry"),
        ("これはいくらですか？", "Kore wa ikura desu ka?", "How much is this?"),
        ("トイレはどこですか？", "Toire wa doko desu ka?", "Where is the toilet?"),
        ("英語を話せますか？", "Eigo wo hanasemasu ka?", "Can you speak English?"),
        ("メニューをください", "Menyuu wo kudasai", "Please give me the menu"),
        ("おすすめは何ですか？", "Osusume wa nan desu ka?", "What do you recommend?"),
        ("水をください", "Mizu wo kudasai", "Please give me water"),
        ("駅はどこですか？", "Eki wa doko desu ka?", "Where is the train station?"),
        ("写真を撮ってもいいですか？", "Shashin wo totte mo ii desu ka?", "May I take a photo?"),
        ("おいしい！", "Oishii!", "Delicious!"),
        ("いただきます", "Itadakimasu", "Said before eating (let's eat)"),
        ("ごちそうさまでした", "Gochisousama deshita", "Said after eating (thank you for the meal)"),
        ("一枚ください", "Ichimai kudasai", "One ticket please"),
        ("右", "Migi", "Right"),
        ("左", "Hidari", "Left"),
        ("まっすぐ", "Massugu", "Straight ahead"),
        ("助けてください", "Tasukete kudasai", "Please help me"),
        ("クレジットカードは使えますか？", "Kurejitto kaado wa tsukaemasu ka?", "Can I use a credit card?"),
        ("袋はいりません", "Fukuro wa irimasen", "I don't need a bag"),
        ("これをください", "Kore wo kudasai", "I'll have this please"),
        ("乾杯！", "Kanpai!", "Cheers!"),
        ("おやすみなさい", "Oyasumi nasai", "Good night"),
        ("はい / いいえ", "Hai / Iie", "Yes / No"),
        ("わかりません", "Wakarimasen", "I don't understand"),
    ]
    jp, romaji, english = random.choice(phrases)
    embed = discord.Embed(title="🗣️ Japanese Phrase", color=0xE60026)
    embed.add_field(name="Japanese", value=f"**{jp}**", inline=False)
    embed.add_field(name="Pronunciation", value=f"*{romaji}*", inline=True)
    embed.add_field(name="Meaning", value=english, inline=True)
    embed.set_footer(text="Use /phrase again for another one!")
    await interaction.response.send_message(embed=embed)


active_quizzes = {}

@tree.command(name="quiz", description="Japan & geography trivia from the internet! 🧠")
async def quiz(interaction: discord.Interaction):
    import random
    import html

    await interaction.response.defer()

    # Try Japan-specific first (category 19 = Science: Nature, not perfect but we rotate)
    # Use category 22 = Geography for broad trivia, occasionally pull Japan questions
    urls = [
        "https://opentdb.com/api.php?amount=1&category=22&difficulty=medium&type=multiple",  # Geography
        "https://opentdb.com/api.php?amount=1&category=23&difficulty=medium&type=multiple",  # History
        "https://opentdb.com/api.php?amount=1&type=multiple",  # Any category fallback
    ]
    data = {}
    for url in urls:
        data = fetch_json(url)
        if data.get("results"):
            break

    results = data.get("results", [])

    if not results:
        # Fallback to a local question if API fails
        fallback = {
            "q": "What is the capital city of Japan?",
            "options": ["Osaka", "Kyoto", "Tokyo", "Hiroshima"],
            "answer": 2,
        }
        question_text = fallback["q"]
        options       = fallback["options"]
        correct       = options[fallback["answer"]]
    else:
        result        = results[0]
        question_text = html.unescape(result["question"])
        correct       = html.unescape(result["correct_answer"])
        incorrects    = [html.unescape(a) for a in result["incorrect_answers"]]
        options       = incorrects + [correct]
        random.shuffle(options)

    letters = ["🇦", "🇧", "🇨", "🇩"]
    correct_idx = options.index(correct)

    embed = discord.Embed(title="🧠 Trivia Quiz", description=f"**{question_text}**", color=0xE60026)
    for i, opt in enumerate(options):
        embed.add_field(name=f"{letters[i]} {opt}", value="", inline=False)
    embed.set_footer(text="Click a button to answer! · 30 seconds")

    class QuizView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=30)
            for i, opt in enumerate(options):
                btn = discord.ui.Button(
                    label=f"{letters[i]} {opt}",
                    custom_id=str(i),
                    style=discord.ButtonStyle.secondary
                )
                btn.callback = self.make_callback(i)
                self.add_item(btn)

        def make_callback(self, idx):
            async def callback(btn_interaction: discord.Interaction):
                for item in self.children:
                    item.disabled = True
                if idx == correct_idx:
                    result_text = f"✅ Correct! The answer was **{correct}**."
                    colour = 0x00FF00
                else:
                    result_text = f"❌ Wrong! The correct answer was **{correct}**."
                    colour = 0xFF0000
                result_embed = discord.Embed(
                    title="🧠 Trivia Quiz — Result",
                    description=result_text,
                    color=colour
                )
                await btn_interaction.response.edit_message(embed=result_embed, view=self)
            return callback

    await interaction.followup.send(embed=embed, view=QuizView())



@tree.command(name="convert", description="Convert any amount of GBP or AUD to JPY 💴")
@app_commands.describe(amount="The amount to convert", currency="GBP or AUD")
@app_commands.choices(currency=[
    app_commands.Choice(name="GBP 🇬🇧", value="GBP"),
    app_commands.Choice(name="AUD 🇦🇺", value="AUD"),
])
async def convert(interaction: discord.Interaction, amount: float, currency: str):
    await interaction.response.defer()

    flag = "🇬🇧" if currency == "GBP" else "🇦🇺"
    url  = f"https://open.er-api.com/v6/latest/{currency}"
    data = fetch_json(url)
    rate = data.get("rates", {}).get("JPY")

    if rate:
        result = amount * rate
        embed  = discord.Embed(title=f"💴 {flag} {currency} → JPY", color=0xE60026)
        embed.add_field(
            name="Result",
            value=f"**{amount:,.2f} {currency} = ¥{result:,.0f}**",
            inline=False,
        )
        embed.add_field(name="Rate", value=f"1 {currency} = ¥{rate:,.2f}", inline=True)
        embed.set_footer(text=f"Updated: {datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')} · Powered by ExchangeRate-API")
    else:
        embed = discord.Embed(title="❌ Error", description="Could not fetch exchange rate. Try again later.", color=0xFF0000)

    await interaction.followup.send(embed=embed)


# ── Random commands ──────────────────────

JAPANESE_FOODS = [
    ("Ramen 🍜", "Hokkaido", "A rich noodle soup with various broths — miso, soy, or pork-based tonkotsu. Every region has its own style."),
    ("Sushi 🍣", "Tokyo (Edo)", "Vinegared rice topped with fresh fish or seafood. Edomae-style sushi originated in Tokyo in the 19th century."),
    ("Takoyaki 🐙", "Osaka", "Ball-shaped snacks made of wheat batter filled with diced octopus, tempura scraps, and ginger. A street food staple."),
    ("Okonomiyaki 🥞", "Osaka / Hiroshima", "A savoury pancake filled with cabbage, meat or seafood, topped with mayo and okonomiyaki sauce. Often called 'Japanese pizza'."),
    ("Tempura 🍤", "Tokyo", "Lightly battered and deep-fried seafood or vegetables. The batter is kept cold for a delicate, crispy texture."),
    ("Yakitori 🍢", "Nationwide", "Skewered chicken grilled over charcoal. Every part of the chicken is used — thigh, skin, liver, heart and more."),
    ("Tonkatsu 🥩", "Tokyo", "A breaded and deep-fried pork cutlet served with shredded cabbage and a thick Worcestershire-based sauce."),
    ("Udon 🍜", "Kagawa", "Thick wheat noodles served hot or cold in a mild dashi broth. Kagawa prefecture is considered the udon capital of Japan."),
    ("Soba 🍜", "Nagano", "Thin buckwheat noodles served hot in broth or cold with a dipping sauce. Popular in mountain regions."),
    ("Onigiri 🍙", "Nationwide", "Rice balls wrapped in nori with fillings like salmon, tuna mayo, or pickled plum. The ultimate convenience food."),
    ("Karaage 🍗", "Nationwide", "Japanese fried chicken marinated in soy, ginger and garlic, then fried until crispy. Often served with lemon and mayo."),
    ("Gyoza 🥟", "Utsunomiya", "Pan-fried dumplings filled with pork and cabbage. Utsunomiya city holds an annual gyoza festival celebrating them."),
    ("Shabu-Shabu 🥘", "Osaka", "Thinly sliced meat swirled in a hot pot of kombu broth, then dipped in ponzu or sesame sauce."),
    ("Matcha Desserts 🍵", "Kyoto / Uji", "Uji in Kyoto is the matcha capital of Japan — matcha ice cream, mochi, parfaits and cakes are everywhere."),
    ("Taiyaki 🐟", "Nationwide", "Fish-shaped waffles filled with sweet red bean paste, custard, or chocolate. A beloved street food snack."),
    ("Yakisoba 🍜", "Nationwide", "Stir-fried wheat noodles with pork, cabbage and vegetables, seasoned with a tangy sauce. A festival staple."),
    ("Miso Soup 🍵", "Nationwide", "A traditional soup made from fermented soybean paste with tofu, seaweed and spring onion. Served with almost every meal."),
    ("Kaiseki 🍱", "Kyoto", "A multi-course fine dining experience featuring seasonal ingredients. Considered the pinnacle of Japanese cuisine."),
    ("Natto 🫘", "Ibaraki", "Fermented soybeans with a sticky texture and strong smell. Divisive even among Japanese people — but incredibly nutritious."),
    ("Conveyor Belt Sushi 🍣", "Osaka", "Kaiten-zushi — sushi served on a rotating conveyor belt. Invented in Osaka in 1958, now found across the country."),
]

JAPANESE_WORDS = [
    ("木漏れ日", "Komorebi", "noun", "The interplay of light and leaves — sunlight filtering through trees.", "木漏れ日が美しい (Komorebi ga utsukushii) — The sunlight through the trees is beautiful."),
    ("侘寂", "Wabi-sabi", "philosophy", "Finding beauty in imperfection, impermanence, and incompleteness.", "日本の陶器には侘寂がある — Japanese pottery has wabi-sabi."),
    ("積ん読", "Tsundoku", "noun", "Buying books and letting them pile up unread.", "また積ん読が増えた — My tsundoku pile has grown again."),
    ("なつかしい", "Natsukashii", "adjective", "A bittersweet nostalgic feeling for the past.", "この曲はなつかしい — This song makes me nostalgic."),
    ("一期一会", "Ichi-go ichi-e", "phrase", "Treasure every encounter, as it will never recur. A tea ceremony concept.", "一期一会の精神で生きる — Live by the spirit of ichi-go ichi-e."),
    ("頑張る", "Ganbaru", "verb", "To persist, do your best, give it your all. One of the most used words in Japanese.", "頑張れ！(Ganbare!) — Do your best! / You've got this!"),
    ("物の哀れ", "Mono no aware", "phrase", "The bittersweet awareness of impermanence — like cherry blossoms falling.", "桜の散る様子に物の哀れを感じる — The falling cherry blossoms evoke mono no aware."),
    ("甘える", "Amaeru", "verb", "To depend on someone's goodwill or indulge in their kindness.", "子供が親に甘える — A child depends on their parent's affection."),
    ("空気を読む", "Kuuki wo yomu", "phrase", "Literally 'read the air' — to pick up on unspoken social cues.", "空気を読んで静かにした — I read the room and stayed quiet."),
    ("縁側", "Engawa", "noun", "The narrow wooden veranda on the outside of a traditional Japanese house.", "縁側でお茶を飲む — Drink tea on the engawa."),
    ("花見", "Hanami", "noun", "The tradition of gathering under cherry blossom trees to appreciate their beauty.", "来週花見をしよう！— Let's do hanami next week!"),
    ("間", "Ma", "noun", "Negative space or pause — the meaningful gap between things in art, music or conversation.", "音楽の間が大切だ — The pause in music is important."),
    ("おつかれさま", "Otsukaresama", "phrase", "Said to someone after hard work — 'you must be tired' / 'well done'. Has no direct English equivalent.", "おつかれさまでした！— Great work today!"),
    ("引きこもり", "Hikikomori", "noun", "Acute social withdrawal — staying isolated at home for months or years.", "引きこもりは社会問題だ — Hikikomori is a social issue."),
    ("木漏れ日", "Komorebi", "noun", "The interplay of light and leaves when sunlight filters through trees.", "木漏れ日の中を歩く — Walking through the komorebi."),
]


@tree.command(name="food", description="Random Japanese dish — what to eat in Japan 🍜")
async def food(interaction: discord.Interaction):
    import random
    name, region, description = random.choice(JAPANESE_FOODS)
    embed = discord.Embed(title=f"🍽️ Japanese Food: {name}", description=description, color=0xE60026)
    embed.add_field(name="📍 Region", value=region, inline=True)
    embed.set_footer(text="Use /food again for another dish!")
    await interaction.response.send_message(embed=embed)


@tree.command(name="anime", description="Random anime recommendation 🎌")
async def anime(interaction: discord.Interaction):
    await interaction.response.defer()
    import random

    # Jikan API — free, no key needed, based on MyAnimeList
    page = random.randint(1, 30)
    url  = f"https://api.jikan.moe/v4/top/anime?page={page}&limit=5"
    data = fetch_json(url)
    items = data.get("data", [])

    if not items:
        await interaction.followup.send("❌ Couldn't fetch anime right now. Try again in a moment!", ephemeral=True)
        return

    a        = random.choice(items)
    title_en = a.get("title_english") or a.get("title", "Unknown")
    score    = a.get("score", "N/A")
    episodes = a.get("episodes", "?")
    synopsis = a.get("synopsis", "No description available.")
    if len(synopsis) > 300:
        synopsis = synopsis[:300] + "..."
    genres   = ", ".join(g["name"] for g in a.get("genres", [])[:3]) or "N/A"
    year     = a.get("year", "N/A")
    url_mal  = a.get("url", "")
    image    = a.get("images", {}).get("jpg", {}).get("image_url", "")

    embed = discord.Embed(title=f"🎌 {title_en}", description=synopsis, color=0xE60026, url=url_mal)
    embed.add_field(name="⭐ Score",    value=str(score),    inline=True)
    embed.add_field(name="📺 Episodes", value=str(episodes), inline=True)
    embed.add_field(name="📅 Year",     value=str(year),     inline=True)
    embed.add_field(name="🏷️ Genres",   value=genres,        inline=False)
    if image:
        embed.set_thumbnail(url=image)
    embed.set_footer(text="Use /anime again for another! · Data from MyAnimeList")
    await interaction.followup.send(embed=embed)


@tree.command(name="word", description="Random Japanese word with meaning and example 📖")
async def word(interaction: discord.Interaction):
    import random
    kanji, romaji, pos, meaning, example = random.choice(JAPANESE_WORDS)
    embed = discord.Embed(title="📖 Japanese Word", color=0xE60026)
    embed.add_field(name="Word",          value=f"**{kanji}**", inline=True)
    embed.add_field(name="Pronunciation", value=f"*{romaji}*",  inline=True)
    embed.add_field(name="Type",          value=pos,            inline=True)
    embed.add_field(name="Meaning",       value=meaning,        inline=False)
    embed.add_field(name="Example",       value=f"_{example}_", inline=False)
    embed.set_footer(text="Use /word again for another one!")
    await interaction.response.send_message(embed=embed)


async def midnight_ping_loop():
    await client.wait_until_ready()
    while not client.is_closed():
        import zoneinfo
        melb_tz   = zoneinfo.ZoneInfo("Australia/Melbourne")
        now_melb  = datetime.now(melb_tz)

        # Next midnight Melbourne time
        next_midnight_melb = (now_melb + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        wait_seconds = (next_midnight_melb - now_melb).total_seconds()
        await asyncio.sleep(wait_seconds)

        # Find general channel and send ping
        for guild in client.guilds:
            channel = discord.utils.get(guild.text_channels, name=GENERAL_CHANNEL_NAME)
            if channel:
                days_left = (JAPAN_DEPARTURE - datetime.now(timezone.utc)).days
                if days_left > 0:
                    embed = discord.Embed(
                        title="🌙 Daily Japan Countdown",
                        description=f"@everyone **{days_left} days** until Rob leaves for Japan! 🇯🇵✈️",
                        color=0xE60026,
                    )
                    embed.set_footer(text="Use /japan for the full countdown")
                    await channel.send("@everyone", embed=embed)


# ── Bot ready ────────────────────────────

@client.event
async def on_ready():
    await tree.sync()
    await client.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name="🇯🇵 Counting down to Japan"
    ))
    client.loop.create_task(midnight_ping_loop())
    print(f"✅ Logged in as {client.user} (ID: {client.user.id})")
    print(f"   Commands: /ping /japan /trip /weather /yen /fact /phrase /quiz /convert /food /anime /word")
    print(f"   Midnight ping active → #{GENERAL_CHANNEL_NAME}")

client.run(BOT_TOKEN)
