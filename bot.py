import discord
from discord.ext import commands
import os
import requests
import openai
from dotenv import load_dotenv

load_dotenv()

# Load API keys from environment
TOKEN = os.getenv("TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

# Setup Discord bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Banned words (customize as needed)
banned_words = ["badword1", "badword2", "slur1"]


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


async def moderate_message(content):
    try:
        response = openai.Moderation.create(input=content)
        result = response["results"][0]
        return result["flagged"], result["categories"]
    except Exception as e:
        print(f"⚠️ OpenAI moderation error: {e}")
        return False, {}


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()

    if any(word in content for word in banned_words):
        await message.delete()
        await message.channel.send(f"{message.author.mention}, your message was removed for using banned words.")
        return

    flagged, categories = await moderate_message(message.content)
    if flagged:
        await message.delete()
        reasons = ', '.join([k for k, v in categories.items() if v])
        await message.channel.send(f"{message.author.mention}, your message was flagged for: {reasons}.")
        return

    await bot.process_commands(message)


# 📈 Stock price command — rate limited
@bot.command()
@commands.cooldown(rate=1, per=15, type=commands.BucketType.user)
async def stock(ctx, symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol.upper()}&token={FINNHUB_API_KEY}"
        res = requests.get(url, timeout=5).json()
        if "c" in res and res["c"] != 0:
            await ctx.send(f"📈 {symbol.upper()} price: ${res['c']}")
        else:
            await ctx.send("❌ Invalid stock symbol.")
    except Exception as e:
        print(f"⚠️ Stock error: {e}")
        await ctx.send("⚠️ Couldn't fetch stock data right now.")


# 💰 Crypto price command — rate limited
@bot.command()
@commands.cooldown(rate=1, per=15, type=commands.BucketType.user)
async def crypto(ctx, symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol=BINANCE:{symbol.upper()}USDT&token={FINNHUB_API_KEY}"
        res = requests.get(url, timeout=5).json()
        if "c" in res and res["c"] != 0:
            await ctx.send(f"💰 {symbol.upper()} price: ${res['c']}")
        else:
            await ctx.send("❌ Invalid crypto symbol.")
    except Exception as e:
        print(f"⚠️ Crypto error: {e}")
        await ctx.send("⚠️ Couldn't fetch crypto data right now.")


# 🕒 Cooldown feedback
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Try again in {error.retry_after:.1f} seconds.")
    else:
        raise error


# 🛑 Safe bot start
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Discord TOKEN missing from .env")

