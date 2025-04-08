import discord
from discord.ext import commands
import os
import requests
import openai
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

banned_words = ["badword1", "badword2", "slur1"]  # Replace with your own list


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


async def moderate_message(content):
    try:
        response = openai.Moderation.create(input=content)
        flagged = response["results"][0]["flagged"]
        categories = response["results"][0]["categories"]
        return flagged, categories
    except Exception as e:
        print(f"Moderation error: {e}")
        return False, {}


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    lowered = message.content.lower()
    if any(word in lowered for word in banned_words):
        await message.delete()
        await message.channel.send(f"{message.author.mention}, message removed: banned word.")
        return

    flagged, categories = await moderate_message(message.content)
    if flagged:
        await message.delete()
        reasons = ', '.join([k for k, v in categories.items() if v])
        await message.channel.send(f"{message.author.mention}, message removed due to: {reasons}.")
        return

    await bot.process_commands(message)


@bot.command()
async def stock(ctx, symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol.upper()}&token={FINNHUB_API_KEY}"
    res = requests.get(url).json()
    if "c" in res and res["c"] != 0:
        await ctx.send(f"📈 {symbol.upper()} price: ${res['c']}")
    else:
        await ctx.send("❌ Invalid stock symbol.")


@bot.command()
async def crypto(ctx, symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol=BINANCE:{symbol.upper()}USDT&token={FINNHUB_API_KEY}"
    res = requests.get(url).json()
    if "c" in res and res["c"] != 0:
        await ctx.send(f"💰 {symbol.upper()} price: ${res['c']}")
    else:
        await ctx.send("❌ Invalid crypto symbol.")


bot.run(os.getenv("TOKEN"))
