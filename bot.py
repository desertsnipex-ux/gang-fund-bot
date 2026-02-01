import os
import sqlite3
import discord
from discord.ext import commands
from keep_alive import keep_alive  # optional keep-alive server

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Bot prefix
bot = commands.Bot(command_prefix='!', intents=intents)

# Database setup
DB_PATH = "database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            contributed INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def add_user_if_not_exists(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def get_contributed(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT contributed FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def update_balance(user_id, amount, add_contributed=False):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if add_contributed:
        c.execute("UPDATE users SET balance = balance + ?, contributed = contributed + ? WHERE user_id = ?",
                  (amount, amount, user_id))
    else:
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?",
                  (amount, user_id))
    conn.commit()
    conn.close()

def total_balance():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT SUM(balance) FROM users")
    result = c.fetchone()
    conn.close()
    return result[0] if result[0] else 0

# Events
@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

# Commands
@bot.command()
@commands.has_permissions(administrator=True)
async def add(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("❌ Amount must be positive.")
        return
    add_user_if_not_exists(member.id)
    update_balance(member.id, amount, add_contributed=True)
    await ctx.send(f"✅ Added {amount} coins to {member.mention}'s balance.")

@bot.command()
@commands.has_permissions(administrator=True)
async def take(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("❌ Amount must be positive.")
        return
    add_user_if_not_exists(member.id)
    balance = get_balance(member.id)
    if balance < amount:
        await ctx.send("❌ User does not have enough balance.")
        return
    update_balance(member.id, -amount)
    await ctx.send(f"✅ Took {amount} coins from {member.mention}'s balance.")

@bot.command()
async def balance(ctx, member: discord.Member = None):
    member = member or ctx.author
    add_user_if_not_exists(member.id)
    bal = get_balance(member.id)
    await ctx.send(f"💰 {member.mention} has {bal} coins.")

@bot.command()
async def contributed(ctx, member: discord.Member = None):
    member = member or ctx.author
    add_user_if_not_exists(member.id)
    contrib = get_contributed(member.id)
    await ctx.send(f"📈 {member.mention} has contributed {contrib} coins in total.")

@bot.command()
async def total(ctx):
    total_bal = total_balance()
    await ctx.send(f"💎 Total balance of all users: {total_bal} coins")

# Initialize DB
init_db()

# Start keep-alive server
keep_alive()

# Run bot
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)