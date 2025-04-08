import discord
from discord.ext import commands
import os
import requests
import logging
from dotenv import load_dotenv
import re
from typing import Optional
from flask import Flask, request, jsonify

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot Initialization
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=commands.DefaultHelpCommand()
)

# Configuration from .env file
class Config:
    COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
    FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
    BANNED_WORDS = ["toxicword1", "toxicword2", "toxicword3"]  # Add banned words here
    DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))  # ID of the channel where GitHub updates will be posted

# Helper Functions

async def fetch_crypto_price(crypto_id: str, currency: str = 'usd') -> Optional[float]:
    """Fetch real-time cryptocurrency price from CoinGecko."""
    url = f"{Config.COINGECKO_API_URL}/simple/price?ids={crypto_id}&vs_currencies={currency}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get(crypto_id, {}).get(currency)
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch {crypto_id} price: {e}")
        return None

async def fetch_stock_price(symbol: str) -> Optional[float]:
    """Fetch real-time stock price from Finnhub."""
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={Config.FINNHUB_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("c")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch {symbol} stock price: {e}")
        return None

# Auto Moderation: Block banned words
@bot.event
async def on_message(message):
    """Check for banned words in messages and delete if found."""
    if message.author.bot:
        return

    for word in Config.BANNED_WORDS:
        if re.search(rf"\b{word}\b", message.content, re.IGNORECASE):
            await message.delete()
            await message.channel.send(f"{message.author.mention}, your message was deleted due to inappropriate content.")
            return

    await bot.process_commands(message)  # Allow commands to run normally

# Stock Price Command
@bot.command(name="stock", help="Get real-time stock prices. Example: !stock AAPL")
async def stock(ctx: commands.Context, symbol: str):
    """Fetch real-time stock price."""
    price = await fetch_stock_price(symbol)
    if price is not None:
        embed = discord.Embed(
            title=f"📈 {symbol.upper()} Stock Price",
            description=f"Current price: ${price:,.2f}",
            color=discord.Color.green()
        )
        embed.set_footer(text="Data from Finnhub")
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"❌ Could not fetch stock price for {symbol}.")

# Crypto Price Command
@bot.command(name="crypto", help="Get real-time cryptocurrency price. Example: !crypto bitcoin")
async def crypto(ctx: commands.Context, crypto_id: str, currency: str = 'usd'):
    """Fetch real-time cryptocurrency price."""
    price = await fetch_crypto_price(crypto_id.lower(), currency.lower())
    if price is not None:
        embed = discord.Embed(
            title=f"💰 {crypto_id.upper()} Price",
            description=f"Current price: ${price:,.2f} {currency.upper()}",
            color=discord.Color.green()
        )
        embed.set_footer(text="Data from CoinGecko")
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"❌ Could not fetch price for {crypto_id}.")

# AI Integration (Example Placeholder)
@bot.command(name="ai", help="AI-based moderation or smart tasks. Example: !ai analyze 'message content'")
async def ai(ctx: commands.Context, *, message: str):
    """Placeholder for future AI-powered features."""
    await ctx.send(f"🤖 AI Analysis of: {message}\n(This feature will be implemented soon!)")

# Kick Command
@bot.command(name="kick", help="Kick a user from the server. Usage: !kick @user reason")
async def kick(ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
    """Kick a member from the server."""
    if ctx.author.guild_permissions.kick_members:
        await member.kick(reason=reason)
        await ctx.send(f"✅ Kicked {member.mention} for: {reason}")
    else:
        await ctx.send("❌ You don't have permission to kick members!")

# Ban Command
@bot.command(name="ban", help="Ban a user from the server. Usage: !ban @user reason")
async def ban(ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
    """Ban a member from the server."""
    if ctx.author.guild_permissions.ban_members:
        await member.ban(reason=reason)
        await ctx.send(f"✅ Banned {member.mention} for: {reason}")
    else:
        await ctx.send("❌ You don't have permission to ban members!")

# Unban Command
@bot.command(name="unban", help="Unban a user from the server. Usage: !unban @user")
async def unban(ctx: commands.Context, member: discord.User):
    """Unban a member from the server."""
    if ctx.author.guild_permissions.ban_members:
        await ctx.guild.unban(member)
        await ctx.send(f"✅ Unbanned {member.mention}")
    else:
        await ctx.send("❌ You don't have permission to unban members!")

# GitHub Webhook Listener (Flask)
app = Flask(__name__)

@app.route("/github", methods=["POST"])
def github_webhook():
    """Receive GitHub webhook payload and post to Discord channel."""
    payload = request.json
    if payload is None:
        return jsonify({"message": "Invalid payload"}), 400

    try:
        # Example: Push event handler
        if "pusher" in payload:
            pusher_name = payload["pusher"]["name"]
            commit_message = payload["head_commit"]["message"]
            repo_name = payload["repository"]["name"]
            commit_url = payload["head_commit"]["url"]

            message = f"🚀 **New Push to {repo_name}** by {pusher_name}:\n\n`{commit_message}`\n[View Commit]({commit_url})"
            
            channel = bot.get_channel(Config.DISCORD_CHANNEL_ID)
            if channel:
                bot.loop.create_task(channel.send(message))
            
            return jsonify({"message": "Success"}), 200
        else:
            return jsonify({"message": "Unsupported event"}), 400
    except KeyError as e:
        logger.error(f"Missing expected field in webhook: {e}")
        return jsonify({"message": "Error processing webhook"}), 500

# Bot Events
@bot.event
async def on_ready():
    """Called when bot is ready."""
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name="for toxic words 🚫"
    ))

# Run the bot
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        logger.error("DISCORD_TOKEN environment variable not set!")
        exit(1)

    try:
        # Run the Discord bot
        bot.run(TOKEN)
    except discord.LoginError:
        logger.error("Invalid Discord token")
    except KeyboardInterrupt:
        logger.info("Bot shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

    # Run the Flask app in a separate thread (GitHub Webhook listener)
    app.run(host="0.0.0.0", port=5000)
