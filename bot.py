import discord
from discord.ext import commands
import os
import requests

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

banned_words = ["badword1", "badword2", "slur1"]  # Replace with your own list


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    lowered = message.content.lower()
    if any(word in lowered for word in banned_words):
        await message.delete()
        await message.channel.send(f"{message.author.mention}, your message was removed due to inappropriate content.")
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
