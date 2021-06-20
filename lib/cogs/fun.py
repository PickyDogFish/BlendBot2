from discord.ext.commands import Cog
from discord.ext.commands import command
from random import choice
from ..db import db

class Fun(Cog):
    def __init__(self, bot):
        self.bot=bot

    @command(name="hello", aliases = ["hi", "hey"])
    async def say_hello(self, ctx):
        await ctx.send(f"{choice(('Hello', 'Hi', 'Hey'))} {ctx.author.mention}!")

    @command(name="add")
    async def add_theme(self, ctx, *, themes):
        await ctx.send(themes)

    @command(name="adduser")
    async def add_user_to_db(self, ctx):
        db.execute("INSERT OR IGNORE INTO users (UserID) VALUES (?)", ctx.author.id)
        await ctx.send(f"Added {ctx.author.mention} to the database!")

    @command(name="suggest")
    async def suggest_theme(self, ctx, *, sugg):
        neki = db.execute("SELECT themeName FROM themes WHERE themeName = ?", sugg)
        if (neki == None):
            db.execute("INSERT INTO themes (themeName) VALUES (?)", sugg)
            ctx.send("Thank you for suggesting " + sugg + "!")
        else:
            ctx.send("Theme has already been suggested")

    @Cog.listener()
    async def on_ready(self):
        print("fun cog ready")


def setup(bot):
    bot.add_cog(Fun(bot))