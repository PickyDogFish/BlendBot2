from lib.bot import CUSTOM_SUBMIT_ID, LOG_CHANNEL_ID, SUBMIT_CHANNEL_ID, GUILD_ID
from discord.ext.commands import Cog
from discord.ext.commands import command
from discord import Embed
import discord
from random import choice
from ..db import db
from datetime import date, datetime
from math import sqrt

from PIL import Image, ImageDraw, ImageFont

class Fun(Cog):
    def __init__(self, bot):
        self.bot=bot

    @command(name="hello", aliases = ["hi", "hey"])
    async def say_hello(self, ctx):
        await ctx.send(f"{choice(('Hello', 'Hi', 'Hey'))} {ctx.author.mention}!")

    @command(name="adduser")
    async def add_user_to_db(self, ctx):
        db.execute("INSERT OR IGNORE INTO users (UserID) VALUES (?)", ctx.author.id)
        await ctx.send(f"Added {ctx.author.mention} to the database!")

    @command(name="suggest")
    async def suggest_theme(self, ctx, *, sugg):
        neki = db.field("SELECT themeName FROM themes WHERE themeName = ?", (sugg))
        if (neki == None):
            db.execute("INSERT INTO themes (themeName) VALUES (?)", sugg)
            await ctx.send("Thank you for suggesting " + sugg + "!")
        else:
            await ctx.send("Theme has already been suggested")

    @command(name="random")
    async def random_theme(self, ctx):
        randomTheme = db.field("SELECT themeName FROM themes WHERE themeStatus = 1 ORDER BY RANDOM() LIMIT 1")
        await ctx.send(randomTheme)

    #@command(name="help")
    #async def show_help(self, ctx):
    #    embeded = Embed(title="Daily blend bot help page", colour = 16754726, description = "List of commands, prefix is **$**.")
    #    embeded.add_field(name="$help", value="Displays this help page")
    #    embeded.add_field(name="$suggest [theme]", value="Allows you to suggest a prompt to add to the pool. Suggestions will be manually reviewed.")
    #    embeded.add_field(name="$submit [image/video]", value="Allows you to submit your render for voting")
    #    embeded.add_field(name="$daily", value="Tells the current daily challenge theme")
    #    embeded.add_field(name="$random", value="Tells a random theme")
    #    embeded.add_field(name="$time", value="Tells you how much time is left for the current daily challenge")
    #    await ctx.send(embed = embeded)

    @command(name="help")
    async def show_help(self, ctx):
        helpText = "List of commands, with the prefix **$**:\n"
        helpText += "`$help:` Displays this help page.\n\n"
        helpText += "`$suggest [theme]:` Allows you to suggest a prompt to add to the pool. Suggestions will be manually reviewed.\n\n"
        helpText += "`$submit [image/video]:` Allows you to submit your render for voting.\n\n"
        helpText += "`$daily:` Tells the current daily challenge theme.\n\n"
        helpText += "`$random:` Tells a random theme.\n\n"
        helpText += "`$time:` Tells you how much time is left for the current daily challenge.\n\n"
        helpText += "`$level:` Tells you how much time you have spent on this server.\n\n"
        embeded = Embed(title="Daily blend bot help page", colour = 16754726, description = helpText)
        await ctx.send(embed = embeded)

    @command(name="submit")
    async def submit_daily(self, ctx):
        if ctx.channel.id != SUBMIT_CHANNEL_ID and ctx.channel.id != CUSTOM_SUBMIT_ID:
            await ctx.send("Cannot submit in this channel.")
        #for daily challenge submissions
        elif len(ctx.message.attachments) > 0 and ctx.channel.id == SUBMIT_CHANNEL_ID:
            chalID = db.field("SELECT currentChallengeID FROM currentChallenge WHERE challengeTypeID = 0")
            if (db.field("SELECT msgID FROM submission WHERE challengeID = ? AND userID = ?", chalID, ctx.author.id) == None):
                db.execute("INSERT INTO submission (userID, msgID, challengeID) VALUES (?, ?, ?)", ctx.author.id, ctx.message.id, chalID)
            else:
                db.execute("UPDATE submission SET msgID = ? WHERE challengeID = ? AND userID = ?", ctx.message.id, chalID, ctx.author.id)
            await ctx.message.add_reaction("✅")
        #for custom challenge submissions
        elif len(ctx.message.attachments) > 0 and ctx.channel.id == CUSTOM_SUBMIT_ID:
            challengeID = db.field("SELECT currentChallengeID FROM currentChallenge WHERE challengeTypeID = 2")
            if db.field("SELECT endDate FROM challenge WHERE challengeID = ?", challengeID) < datetime.utcnow().isoformat(timespec='seconds', sep=' '):
                await ctx.send("No custom challenges currently active.")
            else:
                if (db.field("SELECT msgID FROM submission WHERE challengeID = ? AND userID = ?", challengeID, ctx.author.id) == None):
                    db.execute("INSERT INTO submission (userID, msgID, challengeID) VALUES (?, ?, ?)", ctx.author.id, ctx.message.id, challengeID)
                else:
                    db.execute("UPDATE submission SET msgID = ? WHERE challengeID = ? AND userID = ?", ctx.message.id, challengeID, ctx.author.id)
                await ctx.message.add_reaction("✅")

    @command(name="daily")
    async def show_daily(self, ctx):
        await ctx.send(await self.bot.get_daily_theme())

    @command(name="time")
    async def show_time_left(self, ctx):
        now = datetime.now()
        nekiure = (5 - now.hour) % 24
        nekimin = 60 - now.minute
        await ctx.send("You have " + str(nekiure) + " hours and " + str(nekimin) + " minutes left!")

    @command(name="oldlevel")
    async def show_level(self,ctx):
        msgXP, renderXP = db.record("SELECT msgXP, renderXP FROM users WHERE userID = ?", ctx.author.id)
        (renderLvl, renderLeftoverXP, renderStep) = await self.calculate_render_level(renderXP)
        renderProgress = int(renderLeftoverXP/renderStep * 10)
        (msgLevel, msgProgress) = await self.calculate_msg_level(msgXP)
        string = ""
        msgstring = ""
        for i in range(1, 10, 1):
            if i <= renderProgress:
                string += ":green_square:"
            else:
                string += ":white_small_square:"
        for i in range(1, 10, 1):
            if i <= msgProgress:
                msgstring += ":green_square:"
            else:
                msgstring += ":white_small_square:"

        embeded = Embed(colour = 0x6EA252, description = "Render level: **" + str(renderLvl) + "**⠀⠀⠀*" + str(renderLeftoverXP) + "/" + str(renderStep) + "*\n\n" + string)
        embeded.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embeded)

    async def calculate_render_level(self, xp):
        level = 0
        step = 20
        while xp-step >= 0:
            xp = xp-step
            level += 1
            step += 6
        return (level, xp, step)

    async def calculate_msg_level(self,xp):
        return (int(sqrt(xp*10)//10), sqrt(xp*10)%10)


    @command(name="level")
    async def make_level_image(self, ctx, username=None):
        user = None

        if username:
            try:
                int(username[3:-1])
                print(username + " -> " + username[3:-1])
                user = self.bot.get_user(int(username[3:-1]))
            except:
                user = self.bot.get_guild(GUILD_ID).get_member_named(username)
        else:
            user = ctx.author

        if not user:
            await self.bot.get_channel(LOG_CHANNEL_ID).send(f"ERROR: could not retrieve user: {username} -> {username[3:-1]}")
            await ctx.send("Could not retrieve the user.")
            return
        if user.bot:
            await ctx.send("This user is a bot.")
            return

        renderXP = db.field("SELECT renderXP FROM users WHERE userID = ?", user.id)
        (renderLvl, renderLeftoverXP, renderStep) = await self.calculate_render_level(renderXP)
        renderProgress = int(renderLeftoverXP/renderStep * 10) + 1 

        img = Image.new('RGB', (480, 148), color = (30, 30, 30))
        await user.avatar_url_as(format="png", size=128).save(fp="img/pfp.png")
        pfp = Image.open("img/pfp.png", "r")
        img.paste(pfp, (10,10))

        fnt = ImageFont.truetype('fonts/arial.ttf', 40)
        d = ImageDraw.Draw(img)
        d.text((148,10), user.name, font=ImageFont.truetype('fonts/arial.ttf', 30), fill=(230, 230, 230))
        small_fnt = ImageFont.truetype('fonts/arial.ttf', 20)
        place = db.field("SELECT COUNT(userID) FROM users WHERE renderXP >= ?", renderXP)
        d.text((148,115), "Rank:            lvl:        xp: ", font=small_fnt, fill=(230, 230, 230))
        d.text((210,107), "#" + str(place), font=ImageFont.truetype('fonts/arial.ttf', 30), fill=(230, 230, 230))
        d.text((375,107), str(renderLeftoverXP) + "/" + str(renderStep) + "       " , font=ImageFont.truetype('fonts/arial.ttf', 30), fill=(230, 230, 230))
        d.text((300,107), str(renderLvl), font=ImageFont.truetype('fonts/arial.ttf', 30), fill=(230, 230, 230))

        
        d.rectangle((145, 57, 396, 93), fill=(50,50,50))
        
        xpBarX = 148
        for i in range(0, renderProgress):
            d.rectangle((xpBarX, 60, xpBarX+20, 90), fill='lightblue')
            xpBarX += 25

        


        img.save('img/level.png')
        with open('img/level.png', 'rb') as f:
            pic = discord.File(f)
            await ctx.send(file=pic)

    @command(name="giverole")
    async def giverole(self, ctx, roleName):
        if roleName.lower() == "blender":
            await self.bot.add_roles(ctx.message.author, 868864580007374898)
            await ctx.send("Assigned role Blender")
        elif roleName.lower() == "maya":
            await self.bot.add_roles(ctx.message.author, 868864631156928593)
            await ctx.send("Assigned role Maya")
        elif roleName.lower() == "c4d":
            await self.bot.add_roles(ctx.message.author, 868864693069025291)
            await ctx.send("Assigned role C4D")
        else:
            await ctx.send("Cant find role named \"" + roleName + "\"")

    @command(name="removerole")
    async def giverole(self, ctx, roleName):
        if roleName.lower() == "blender":
            await self.bot.remove_roles(ctx.message.author, 868864580007374898)
            await ctx.send("Removed role Blender")
        elif roleName.lower() == "maya":
            await self.bot.remove_roles(ctx.message.author, 868864631156928593)
            await ctx.send("Removed role Maya")
        elif roleName.lower() == "c4d":
            await self.bot.remove_roles(ctx.message.author, 868864693069025291)
            await ctx.send("Removed role C4D")
        else:
            await ctx.send("Cant find role named \"" + roleName + "\"")

            
    @Cog.listener()
    async def on_ready(self):
        print("fun cog ready")


def setup(bot):
    bot.remove_command('help')
    bot.add_cog(Fun(bot))