import os
import sqlite3
import discord
from discord.ext import commands
from discord.ui import View, Button
from keep_alive import keep_alive  # optional for Replit

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)  # custom help

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
# Helper for Embeds
# -------------------------
def create_embed(title, description, color=0x00ff00):
    return discord.Embed(title=title, description=description, color=color)

# -------------------------
# Interactive View
# -------------------------
class BalanceView(View):
    def __init__(self, user):
        super().__init__(timeout=None)
        self.user = user

    @discord.ui.button(label="💰 Check Balance", style=discord.ButtonStyle.green)
    async def balance_button(self, interaction: discord.Interaction, button: Button):
        add_user_if_not_exists(self.user.id)
        bal = get_balance(self.user.id)
        await interaction.response.send_message(embed=create_embed("Balance", f"{self.user.mention} has {bal} coins."), ephemeral=True)

    @discord.ui.button(label="📈 Check Contributions", style=discord.ButtonStyle.blurple)
    async def contrib_button(self, interaction: discord.Interaction, button: Button):
        add_user_if_not_exists(self.user.id)
        contrib = get_contributed(self.user.id)
        await interaction.response.send_message(embed=create_embed("Contributions", f"{self.user.mention} has contributed {contrib} coins in total."), ephemeral=True)

    @discord.ui.button(label="💎 Total Gang Fund", style=discord.ButtonStyle.gold)
    async def total_button(self, interaction: discord.Interaction, button: Button):
        total_bal = total_balance()
        await interaction.response.send_message(embed=create_embed("Gang Fund Total", f"Total balance of all users: {total_bal} coins"), ephemeral=True)

# -------------------------
# Commands
# -------------------------
@bot.command()
async def menu(ctx):
    """Show interactive menu with buttons."""
    view = BalanceView(ctx.author)
    await ctx.send(embed=create_embed("Gang Fund Menu", "Click a button below to interact with the bot!"), view=view)

# Optional: keep old commands if you want
# @bot.command() ...

# -------------------------
# Initialize
# -------------------------
init_db()
keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
