import discord
from discord import app_commands
from datetime import datetime, timezone
import asyncio

# ─────────────────────────────────────────
# CONFIG — edit these
# ─────────────────────────────────────────
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Your Japan departure — QF79, 25 May 2026
# Set the exact departure time (Melbourne local = UTC+10 in May, AEST)
JAPAN_DEPARTURE = datetime(2026, 5, 25, 10, 0, 0, tzinfo=timezone.utc)  # adjust hour if you know exact time
JAPAN_RETURN    = datetime(2026, 6, 12, 0, 0, 0, tzinfo=timezone.utc)   # QF80 return

TRIP_DAYS = 18  # 25 May → 12 June
# ─────────────────────────────────────────

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


def build_countdown_embed() -> discord.Embed:
    now = datetime.now(timezone.utc)
    delta = JAPAN_DEPARTURE - now

    if delta.total_seconds() < 0:
        # Already in Japan or returned
        return_delta = JAPAN_RETURN - now
        if return_delta.total_seconds() > 0:
            d = return_delta.days
            h, rem = divmod(int(return_delta.total_seconds()) % 86400, 3600)
            m, s   = divmod(rem, 60)
            embed = discord.Embed(
                title="🇯🇵 Rob is in Japan RIGHT NOW!",
                description=f"The trip is underway — enjoy every second! 🎌",
                color=0xE60026,  # Japan red
            )
            embed.add_field(name="⏳ Time left in Japan", value=f"`{d}d {h}h {m}m {s}s`", inline=False)
            embed.add_field(name="✈️ Return flight", value="QF80 → Melbourne", inline=True)
            embed.add_field(name="🏔️ Trip length", value=f"{TRIP_DAYS} days", inline=True)
            embed.set_footer(text="Ride some powder for me 🤙")
            return embed
        else:
            embed = discord.Embed(
                title="🏠 Rob is back from Japan",
                description="Trip complete. Start planning the next one.",
                color=0x7289DA,
            )
            embed.set_footer(text="Sayonara, Japan 👋")
            return embed

    # Still counting down
    total_seconds = int(delta.total_seconds())
    days          = delta.days
    hours, rem    = divmod(total_seconds % 86400, 3600)
    minutes, secs = divmod(rem, 60)

    # Weeks / months breakdown
    weeks         = days // 7
    remaining_days = days % 7
    months        = days // 30

    # Progress bar (departure date is the end, today is start)
    trip_announced = datetime(2025, 11, 1, tzinfo=timezone.utc)  # approx when planned
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

    embed.add_field(
        name="⏳ Time Remaining",
        value=f"```{days}d  {hours}h  {minutes}m  {secs}s```",
        inline=False,
    )
    embed.add_field(name="📅 Days",    value=f"`{days}`",    inline=True)
    embed.add_field(name="📆 Weeks",   value=f"`{weeks}w {remaining_days}d`", inline=True)
    embed.add_field(name="🗓️ Months",  value=f"`~{months} months`", inline=True)

    embed.add_field(
        name=f"🚀 Trip Progress  {progress_pct}%",
        value=f"`{bar}`",
        inline=False,
    )

    embed.add_field(name="🛫 Outbound",  value="QF79 · Points upgrade confirmed ✅", inline=True)
    embed.add_field(name="🛬 Return",    value="QF80 · Bid Now upgrade 🤞",          inline=True)

    embed.set_footer(text=f"Last updated: {now.strftime('%d %b %Y %H:%M UTC')} · Ganbatte Rob! 🇯🇵")
    return embed


# ── Slash commands ──────────────────────────────────────

@tree.command(name="ping", description="Check the bot is alive (also earns you the Active Developer badge!)")
async def ping(interaction: discord.Interaction):
    latency = round(client.latency * 1000)
    await interaction.response.send_message(
        f"🏓 Pong! Latency: **{latency}ms**\n"
        f"-# Use this command once, wait 24h, then claim your Active Developer badge at discord.com/developers/active-developer",
        ephemeral=True,
    )


@tree.command(name="japan", description="How long until Rob leaves for Japan? 🇯🇵")
async def japan(interaction: discord.Interaction):
    embed = build_countdown_embed()
    await interaction.response.send_message(embed=embed)


@tree.command(name="trip", description="Full trip details — flights, skis, upgrades")
async def trip(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🗾 Rob's Japan Trip 2026 — Full Details",
        color=0xE60026,
    )
    embed.add_field(name="📅 Dates",        value="25 May → 12 June 2026 (18 days)", inline=False)
    embed.add_field(name="✈️ Outbound",      value="QF79 Melbourne → Tokyo\nPoints upgrade: **Confirmed** ✅", inline=True)
    embed.add_field(name="✈️ Return",        value="QF80 Tokyo → Melbourne\nBid Now upgrade: **Pending** 🤞", inline=True)
    embed.add_field(name="🏔️ Activities",    value="Exploring · Food · Culture · Travel", inline=True)
    embed.set_footer(text="Japan 2026 🇯🇵")
    await interaction.response.send_message(embed=embed)


# ── Bot ready ───────────────────────────────────────────

@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {client.user} (ID: {client.user.id})")
    print(f"   Slash commands synced globally.")
    print(f"   Use /ping to earn the Active Developer badge!")
    print(f"   Use /japan for the countdown.")

client.run(BOT_TOKEN)
