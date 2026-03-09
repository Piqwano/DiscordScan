import discord
from discord import app_commands
import asyncio
import aiohttp
import re
import logging
from datetime import datetime

# ─── CONFIG ───────────────────────────────────────────────────────────────────
DISCORD_TOKEN = "MTQ4MDU2OTcwNDI1Mzc1MTQ3Ng.GIOXrz.gnOjAhlx858CmUbwCjeU6m0aGAqLhnFPTnW7oo"       # <-- paste your bot token here
CHANNEL_ID    = 1480573121634504829             # <-- paste your channel ID here (integer)

AMAZON_URL    = "https://www.amazon.co.uk/dp/B0CCZ1L489"
PRICE_TARGET  = 250.00                          # notify when price drops below this
CHECK_EVERY   = 3600                            # seconds between checks (default: 1 hour)
# ──────────────────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


async def fetch_price(session: aiohttp.ClientSession) -> tuple[float | None, str]:
    """Return (price_float, title_str) or (None, '') on failure."""
    try:
        async with session.get(AMAZON_URL, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=20)) as resp:
            if resp.status != 200:
                log.warning("HTTP %s fetching Amazon page", resp.status)
                return None, ""
            html = await resp.text()
    except Exception as e:
        log.error("Request error: %s", e)
        return None, ""

    # --- price ---
    # Amazon uses several possible patterns; try them in order
    price = None
    patterns = [
        r'<span class="a-offscreen">\s*£([\d,]+\.?\d*)\s*</span>',
        r'"priceAmount"\s*:\s*([\d.]+)',
        r'<span[^>]*class="[^"]*a-price-whole[^"]*"[^>]*>([\d,]+)',
    ]
    for pat in patterns:
        m = re.search(pat, html)
        if m:
            try:
                price = float(m.group(1).replace(",", ""))
                break
            except ValueError:
                continue

    # --- title ---
    title = ""
    tm = re.search(r'<span id="productTitle"[^>]*>\s*(.*?)\s*</span>', html, re.DOTALL)
    if tm:
        title = re.sub(r'\s+', ' ', tm.group(1)).strip()

    return price, title


class PriceTrackerBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.notified_low = False
        self.last_price = None
        self.http_session: aiohttp.ClientSession | None = None

    async def setup_hook(self):
        # Sync slash commands globally (takes up to 1hr to appear everywhere)
        await self.tree.sync()
        log.info("Slash commands synced globally")

    async def on_ready(self):
        log.info("Logged in as %s (ID: %s)", self.user, self.user.id)
        self.http_session = aiohttp.ClientSession()
        self.loop.create_task(self.price_loop())

    async def close(self):
        if self.http_session:
            await self.http_session.close()
        await super().close()

    async def price_loop(self):
        await self.wait_until_ready()
        channel = self.get_channel(CHANNEL_ID)
        if channel is None:
            log.error("Could not find channel %s — check CHANNEL_ID", CHANNEL_ID)
            return

        await channel.send(
            f"🤖 **Amazon Price Tracker started!**\n"
            f"📦 Tracking: <{AMAZON_URL}>\n"
            f"🎯 Will alert when price drops **below £{PRICE_TARGET:.2f}**\n"
            f"🔁 Checking every **{CHECK_EVERY // 60} minutes**\n"
            f"💡 Use `/price` to check the current price anytime!"
        )

        while not self.is_closed():
            price, title = await fetch_price(self.http_session)
            now = datetime.now().strftime("%d %b %Y %H:%M")

            if price is None:
                log.warning("Could not parse price at %s", now)
                await asyncio.sleep(CHECK_EVERY)
                continue

            log.info("Price: £%.2f  (target <£%.2f)  [%s]", price, PRICE_TARGET, now)

            if price < PRICE_TARGET and not self.notified_low:
                embed = discord.Embed(
                    title="🚨 Price Alert! Below your target!",
                    url=AMAZON_URL,
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow(),
                )
                embed.add_field(name="Product",       value=title or "Amazon product",       inline=False)
                embed.add_field(name="Current Price", value=f"**£{price:.2f}**",             inline=True)
                embed.add_field(name="Your Target",   value=f"£{PRICE_TARGET:.2f}",          inline=True)
                embed.add_field(name="You save",      value=f"£{PRICE_TARGET - price:.2f}",  inline=True)
                embed.set_footer(text="Amazon UK • Price Tracker")
                await channel.send(embed=embed)
                self.notified_low = True

            elif price >= PRICE_TARGET and self.notified_low:
                self.notified_low = False
                await channel.send(
                    f"📈 Price is back up to **£{price:.2f}** (above £{PRICE_TARGET:.2f} target). Watching…"
                )

            if self.last_price != price:
                log.info("Price changed: £%s → £%.2f", self.last_price, price)
                self.last_price = price

            await asyncio.sleep(CHECK_EVERY)


bot = PriceTrackerBot()


@bot.tree.command(name="price", description="Check the current Amazon price of the tracked item")
async def slash_price(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)  # shows "Bot is thinking..."

    price, title = await fetch_price(bot.http_session)

    if price is None:
        await interaction.followup.send(
            "❌ Couldn't fetch the price right now — Amazon may be rate limiting. Try again in a moment."
        )
        return

    status = "✅ **Below target! Buy now!**" if price < PRICE_TARGET else f"⏳ Waiting to drop below £{PRICE_TARGET:.2f}"
    color  = discord.Color.green() if price < PRICE_TARGET else discord.Color.orange()

    embed = discord.Embed(title="📦 Current Price Check", url=AMAZON_URL, color=color, timestamp=datetime.utcnow())
    embed.add_field(name="Product", value=title or "Amazon product", inline=False)
    embed.add_field(name="Price",   value=f"**£{price:.2f}**",       inline=True)
    embed.add_field(name="Target",  value=f"£{PRICE_TARGET:.2f}",    inline=True)
    embed.add_field(name="Status",  value=status,                    inline=False)
    embed.set_footer(text="Amazon UK • Price Tracker")

    await interaction.followup.send(embed=embed)


@bot.tree.command(name="status", description="Show tracker status and last known price")
async def slash_status(interaction: discord.Interaction):
    last  = f"£{bot.last_price:.2f}" if bot.last_price else "Not checked yet"
    color = discord.Color.green() if (bot.last_price and bot.last_price < PRICE_TARGET) else discord.Color.blurple()

    embed = discord.Embed(title="🤖 Tracker Status", color=color, timestamp=datetime.utcnow())
    embed.add_field(name="Tracking",    value=f"[Amazon product]({AMAZON_URL})", inline=False)
    embed.add_field(name="Last Price",  value=last,                              inline=True)
    embed.add_field(name="Target",      value=f"£{PRICE_TARGET:.2f}",           inline=True)
    embed.add_field(name="Check Every", value=f"{CHECK_EVERY // 60} minutes",   inline=True)
    embed.set_footer(text="Amazon UK • Price Tracker")

    await interaction.response.send_message(embed=embed)


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
