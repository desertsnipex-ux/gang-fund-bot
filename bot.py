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
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)  # Disable default help

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
        c.execute(
            "UPDATE users SET balance = balance + ?, contributed = contributed + ? WHERE user_id = ?",
            (amount, amount, user_id)
        )
    else:
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def total_balance():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT SUM(balance) FROM users")
    result = c.fetchone()
    conn.close()
    return result[0] if result[0] else 0

# -------------------------
# Custom Embed Helper
# -------------------------
def create_embed(title, description, color=0x00ff00):
    return discord.Embed(title=title, description=description, color=color)

# Events
@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

# -------------------------
# Commands
# -------------------------

@bot.command()
@commands.has_permissions(administrator=True)
async def add(ctx, member: discord.Member, amount: int):
    """Add coins to a user."""
    if amount <= 0:
        await ctx.send(embed=create_embed("Error", "❌ Amount must be positive.", color=0xff0000))
        return
    add_user_if_not_exists(member.id)
    update_balance(member.id, amount, add_contributed=True)
    await ctx.send(embed=create_embed("Balance Updated", f"✅ Added {amount} coins to {member.mention}'s balance."))

@bot.command()
@commands.has_permissions(administrator=True)
async def take(ctx, member: discord.Member, amount: int):
    """Remove coins from a user."""
    if amount <= 0:
        await ctx.send(embed=create_embed("Error", "❌ Amount must be positive.", color=0xff0000))
        return
    add_user_if_not_exists(member.id)
    balance = get_balance(member.id)
    if balance < amount:
        await ctx.send(embed=create_embed("Error", "❌ User does not have enough balance.", color=0xff0000))
        return
    update_balance(member.id, -amount)
    await ctx.send(embed=create_embed("Balance Updated", f"✅ Took {amount} coins from {member.mention}'s balance."))

@bot.command()
async def balance(ctx, member: discord.Member = None):
    """Check user's balance."""
    member = member or ctx.author
    add_user_if_not_exists(member.id)
    bal = get_balance(member.id)
    await ctx.send(embed=create_embed("Balance", f"💰 {member.mention} has {bal} coins."))

@bot.command()
async def contributed(ctx, member: discord.Member = None):
    """Check how much a user has contributed."""
    member = member or ctx.author
    add_user_if_not_exists(member.id)
    contrib = get_contributed(member.id)
    await ctx.send(embed=create_embed("Contributions", f"📈 {member.mention} has contributed {contrib} coins in total."))

@bot.command()
async def total(ctx):
    """Show total balance of all users."""
    total_bal = total_balance()
    await ctx.send(embed=create_embed("Gang Fund Total", f"💎 Total balance of all users: {total_bal} coins"))

@bot.command()
async def help(ctx):
    """Show available commands."""
    embed = discord.Embed(title="🤖 Bot Commands", color=0x00ffff)
    embed.add_field(name="!add @user amount", value="Add coins to a user (admin only).", inline=False)
    embed.add_field(name="!take @user amount", value="Remove coins from a user (admin only).", inline=False)
    embed.add_field(name="!balance [@user]", value="Check your or another user's balance.", inline=False)
    embed.add_field(name="!contributed [@user]", value="Check contributions of a user.", inline=False)
    embed.add_field(name="!total", value="Show total balance of all users.", inline=False)
    embed.add_field(name="!help", value="Show this help message.", inline=False)
    await ctx.send(embed=embed)

# -------------------------
# Initialize DB & Keep-alive
# -------------------------
init_db()
keep_alive()  # optional for Replit
bot.run(os.getenv("DISCORD_TOKEN"))
