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

# Melbourne midnight = 14:00 UTC (AEST = UTC+10)
MIDNIGHT_PING_HOUR_UTC = 14
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
            embed.add_field(
                name=f"{flag} {code} → JPY",
                value=(
                    f"**1 {code} = ¥{rate:,.2f}**\n"
                    f"100 {code} = ¥{rate*100:,.0f}\n"
                    f"500 {code} = ¥{rate*500:,.0f}\n"
                    f"1,000 {code} = ¥{rate*1000:,.0f}"
                ),
                inline=True,
            )
        else:
            embed.add_field(name=f"{flag} {code} → JPY", value="Unavailable", inline=True)

    embed.set_footer(text=f"Updated: {datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')} · Powered by ExchangeRate-API")
    await interaction.followup.send(embed=embed)


@tree.command(name="fact", description="Random Japan fact 🎌")
async def fact(interaction: discord.Interaction):
    import random
    chosen = random.choice(JAPAN_FACTS)
    embed  = discord.Embed(title="🎌 Japan Fact", description=chosen, color=0xE60026)
    embed.set_footer(text="Use /fact again for another one!")
    await interaction.response.send_message(embed=embed)


# ── Midnight ping task ───────────────────

async def midnight_ping_loop():
    await client.wait_until_ready()
    while not client.is_closed():
        now = datetime.now(timezone.utc)

        # Next midnight Melbourne time (UTC+10 in May/June = AEST)
        next_ping = now.replace(hour=MIDNIGHT_PING_HOUR_UTC, minute=0, second=0, microsecond=0)
        if now >= next_ping:
            next_ping += timedelta(days=1)

        wait_seconds = (next_ping - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        # Find the general channel and send the ping
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
    print(f"   Commands: /ping /japan /trip /weather /yen /fact")
    print(f"   Midnight ping active → #{GENERAL_CHANNEL_NAME}")

client.run(BOT_TOKEN)
