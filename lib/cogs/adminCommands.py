import asyncio
import sys
import discord
from discord.ext.commands import Cog
from discord.ext.commands import command
from discord.ext.commands.core import cooldown
from ..db import db
from datetime import date, datetime, timedelta
import json
from lib.bot import LOG_CHANNEL_ID, OWNER_IDS, SUBMIT_CHANNEL_ID
from discord import Embed

class Admin(Cog):
    def __init__(self, bot):
        self.bot=bot

    @Cog.listener()
    async def on_ready(self):
        print("admin cog ready")

    @command(name="addusertodb")
    async def add_user_to_db(self, ctx, userID):
        if ctx.author.guild_permissions.administrator:
            db.execute("INSERT OR IGNORE INTO users (UserID) VALUES (?)", userID)
            await ctx.send(f"Added {userID} to the database!")

    @command(name="clear")
    async def clear(self, ctx, num_of_msgs_to_delete):
        if ctx.author.guild_permissions.administrator:
            list_of_msgs_to_delete = []
            async for message in ctx.channel.history(limit = int(num_of_msgs_to_delete)):
                list_of_msgs_to_delete.append(message)
            await ctx.channel.delete_messages(list_of_msgs_to_delete)
            last_message = [await ctx.channel.send(str(num_of_msgs_to_delete) + " messages were deleted")]
            await asyncio.sleep(2)
            await message.channel.delete_messages(last_message)

    @command(name="kill")
    async def kill(self, ctx):
        if ctx.author.guild_permissions.administrator:
            await ctx.channel.send("See you soon!")
            sys.exit()

    @command(name="reject")
    async def reject(self, ctx, *, theme):
        if ctx.author.guild_permissions.administrator:
            if db.field("SELECT * FROM themes WHERE themeName = ?", theme) != None:
                db.execute("UPDATE themes SET themeStatus = -1 WHERE themeName = ?", theme)
                await ctx.send("Theme status set to rejected")
            else:
                await ctx.send("Theme not found.")

    @command(name="approve")
    async def approve(self, ctx, *, theme):
        if ctx.author.guild_permissions.administrator:
            if db.field("SELECT * FROM themes WHERE themeName = ?", theme) != None:
                db.execute("UPDATE themes SET themeStatus = 1 WHERE themeName = ?", theme)
                await ctx.send("Theme status set to approved")
            else:
                await ctx.send("Theme not found.")

    @command(name="setnotused", aliases = ["setunused"])
    async def not_used(self, ctx, *, theme):
        if ctx.author.guild_permissions.administrator:
            if db.field("SELECT * FROM themes WHERE themeName = ?", theme) != None:
                db.execute("UPDATE themes SET lastUsed = '2011-11-11 11:11:11' WHERE themeName = ?", theme)
                await ctx.send("Theme set to not used")
            else:
                await ctx.send("Theme not found.")
    
    @command(name="setused")
    async def used(self, ctx, *, theme):
        if ctx.author.guild_permissions.administrator:
            if db.field("SELECT * FROM themes WHERE themeName = ?", theme) != None:
                db.execute("UPDATE themes SET lastUsed = ? WHERE themeName = ?", datetime.utcnow().isoformat(timespec='seconds', sep=' '),theme)
                await ctx.send("Theme set to used")
            else:
                await ctx.send("Theme not found.")

    #setdaily <themeName> sets the daily theme to the specified themeName
    @command(name="setdaily")
    async def setdaily(self, ctx, *, theme):
        if ctx.author.guild_permissions.administrator:
            if db.field("SELECT * FROM themes WHERE themeName = ?", theme) != None:
                lastDaily = db.field("SELECT currentChallengeID FROM currentChallenge WHERE challengeTypeID = 0")
                db.execute("UPDATE challenges SET themeName = ? WHERE challengeID = ?", theme, lastDaily)
                db.execute("UPDATE themes SET lastUsed = ? WHERE themeName = ?", datetime.utcnow().isoformat(timespec='seconds', sep=' '), theme)
                await self.bot.get_channel(SUBMIT_CHANNEL_ID).edit(name="Theme-" + theme)
                #await ctx.channel.edit(name="Theme-" + theme)
                await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name = "you make " + theme))
                await ctx.send("The theme has been set to " + theme)
            else:
                await ctx.channel.send("Theme not in pool")

    @command(name="givexp")
    async def givexp(self, ctx, userID, XPamount):
        await self.bot.get_channel(LOG_CHANNEL_ID).send(f"Added {str(XPamount)} XP to {self.bot.get_user(int(userID)).display_name}")
        if ctx.author.guild_permissions.administrator:
            if db.field("SELECT userID FROM users WHERE userID = ?", userID) != None:
                db.execute("UPDATE users SET renderXP = renderXP + ? WHERE userID = ?", XPamount, userID)
                await ctx.send(f"Added {str(XPamount)} XP to {self.bot.get_user(int(userID)).display_name}")
            else:
                await ctx.send("User not in database.")


    #puts the old data into the new database, all paths are hardcoded
    # @command(name="parseolddata")
    # async def parse_old_data(self, ctx):
    #     if ctx.author.guild_permissions.administrator:
    #         await self.parse_user_data(ctx=ctx)
    #         await self.parse_used_themes(ctx=ctx)
    #         await self.parse_themes(ctx=ctx)
    #         await self.parse_suggestions(ctx=ctx)
    #         await ctx.send("Parsed old data")

    # async def parse_user_data(self, ctx):
    #     if ctx.author.guild_permissions.administrator:
    #         with open("D:\BotGit\levels.json", "r+") as file:
    #             data = json.load(file)
    #             for user in data:
    #                 db.execute("INSERT OR IGNORE INTO users (userID, msgXP, renderXP) VALUES (?,?,?)", user, int(data[user]["messagepoints"]), data[user]["dailypoints"])

    # async def parse_themes(self, ctx):
    #     if ctx.author.guild_permissions.administrator:
    #         with open("D:/BotGit/themes.txt", "r") as file:
    #             for line in file:
    #                 db.execute("INSERT OR IGNORE INTO themes (themeName, themeStatus) VALUES (?,1)", line.strip().replace("_", " "))

    # async def parse_used_themes(self, ctx):
    #     if ctx.author.guild_permissions.administrator:
    #         with open("D:/BotGit/usedThemes.txt", "r") as file:
    #             for line in file:
    #                 db.execute("INSERT OR IGNORE INTO themes (themeName, themeStatus, lastUsed) VALUES (?,1,?)", line.strip().replace("_", " "), datetime.utcnow().isoformat())
    
    # async def parse_suggestions(self, ctx):
    #     if ctx.author.guild_permissions.administrator:
    #         with open("D:/BotGit/suggestions.txt", "r") as file:
    #             for line in file:
    #                 db.execute("INSERT OR IGNORE INTO themes (themeName, themeStatus) VALUES (?,0)", line.strip().replace("_", " "))


    #sends a message of max 50 suggested themes
    @command(name="showsuggestions", aliases=["suggestions", "sugg"])
    async def show_suggestions(self, ctx):
        if ctx.author.guild_permissions.administrator:
            listOfSuggestions = db.column("SELECT themeName FROM themes WHERE themeStatus = 0 LIMIT 50")
            await ctx.send(listOfSuggestions)

    #sends a message of all rejected themes
    @command(name="showrejected")
    async def show_rejected(self, ctx):
        if ctx.author.guild_permissions.administrator:
            listOfRejected = db.column("SELECT themeName FROM themes WHERE themeStatus = -1")
            for i in range(50, len(listOfRejected), 50):
                await ctx.send(listOfRejected[i-50:i])
                if i+50 > len(listOfRejected):
                    await ctx.send(listOfRejected[i:])

    #sends a list of all approved themes
    @command(name="showapproved")
    async def show_approved(self, ctx):
        if ctx.author.guild_permissions.administrator:
            listOfApproved= db.column("SELECT themeName FROM themes WHERE themeStatus = 1")
            for i in range(50, len(listOfApproved), 50):
                await ctx.send(listOfApproved[i-50:i])
                if i+50 > len(listOfApproved):
                    await ctx.send(listOfApproved[i:])

    #sends a list of 50 least recently used themes (these are in the pool to be chosen from for the daily challenge)
    @command(name="showthemes", aliases=["themes"])
    async def show_themes(self,ctx):
        if ctx.author.guild_permissions.administrator:
            await ctx.send(db.column("SELECT themeName FROM themes WHERE themeStatus = 1 ORDER BY lastUsed LIMIT 50"))

    @command(name="makelb")
    async def show_leaderboard(self, ctx):
        if ctx.author.guild_permissions.administrator:
            await self.bot.clear_leaderboard()
            await self.bot.make_leaderboard()

    @command(name="dodaily")
    async def run_daily_challenge(self, ctx):
        if ctx.author.guild_permissions.administrator:
            await self.bot.daily_challenge()

    @command(name="setcustom")
    async def set_custom_challenge(self,ctx, name, link, numOfDays, numOfVotingDays):
        if ctx.author.guild_permissions.administrator:
            db.execute("INSERT INTO challenges (challengeTypeID, themeName, startDate, endDate, votingEndDate, imageLink) VALUES (2, ?, ?, ?, ?, ?)", name, (datetime.utcnow() + timedelta(days=1)).isoformat(timespec='seconds', sep=' '), (datetime.utcnow()+timedelta(days=int(numOfDays)+1)).isoformat(timespec='seconds', sep=' '),(datetime.utcnow() + timedelta(days=int(numOfVotingDays) + int(numOfDays)+1)).isoformat(timespec='seconds', sep=' '), link)
            newChallengeID = db.field("SELECT challengeID, themeName FROM challenges WHERE challengeTypeID = 2 ORDER BY challengeID DESC")
            previousChallengeID = db.field("SELECT currentChallengeID FROM currentChallenge WHERE challengeTypeID = 2")
            db.execute("UPDATE currentChallenge SET currentChallengeID = ?, previousChallengeID = ? WHERE challengeTypeID = 2", newChallengeID, previousChallengeID)
            await ctx.send("Set the next custom challenge.")

    @command(name="docustom")
    async def test_custom_challenge(self, ctx):
        if ctx.author.guild_permissions.administrator:
            await self.bot.custom_challenge()


    # @command(name="customSQL")
    # async def run_custom_SQL(self, ctx, *, command):
    #     if ctx.author.id in OWNER_IDS:
    #         await self.bot.get_channel(LOG_CHANNEL_ID).send(ctx.author.name + " just ran custom SQL: " + command)
    #         db.execute(command)

    @command(name="showvoters")
    async def show_voters(self, ctx):
        if ctx.author.id in OWNER_IDS:
            voters = db.records("SELECT voterID, count(votingMsgID) as numOfVotes FROM votes GROUP BY voterID ORDER BY numOfVotes DESC")
            names = ""
            for id, count in voters:
                try:
                    names += self.bot.get_user(id).display_name +": " + str(count) + ", \n"
                except:
                    pass
            await ctx.send(names)

    # @command(name="setisinserver")
    # async def set_isinserver(self,ctx):
    #     if ctx.author.id in OWNER_IDS:
    #         users = db.records("SELECT userID FROM users")
    #         for user in users:
    #             userObject = self.bot.get_user(user[0])
    #             if userObject == None:
    #                 db.execute("UPDATE users SET isInServer = 0 WHERE userID = ?", user[0])

    @command(name="adminhelp")
    async def show_admin_help(self, ctx):
        if ctx.author.guild_permissions.administrator:
            helpText = "List of commands, with the prefix **$**:\n\n\n"
            helpText += "`$clear [number]`: Deletes last *number* messages.\n\n"
            helpText += "`$addusertodb [userId]`: Adds user entry into db with userId. \n\n"
            helpText += "`$reject [theme_name]`: Sets the status of a theme to rejected.\n\n"
            helpText += "`$approve [theme_name]`: Sets the status of a theme to approved.\n\n"
            helpText += "`$setnotused [theme_name]`: sets last used date to 2011-11-11 11:11:11.\n\n"
            helpText += "`$setused [theme_name]`: sets last used to today.\n\n"
            helpText += "`$setdaily [theme_name]`: sets the current daily to theme_name.\n\n"
            helpText += "`$givexp [userID] [xpAmount]`: gives user with userID xpAmount of renderXP. xpAmount can be negative.\n\n"
            helpText += "`$showsuggestions`: shows suggestions without status. also `$sugg` or `$suggestions`.\n\n"
            helpText += "`$showapproved`: shows all approved themes.\n\n"
            helpText += "`$showrejected`: shows all rejected themes.\n\n"
            helpText += "`$showthemes`: shows 50 themes that are in the pool for the next daily.\n\n"
            helpText += "`$makelb`: remakes the leaderboard.\n\n"
            helpText += "`$dodaily`: runs the daily challenge function.\n\n"
            helpText += "`$showvoters`: shows a list of voters.\n\n"
            helpText += "`$setcustom [name] [link] [numOfDays] [numOfVotingDays]`: set things for a custom challenge.\n\n"
            helpText += "`$docustom`: runs the custom challenge function.\n\n"


            embeded = Embed(title="Admin help for 3Daily bot.", colour = 16754726, description = helpText)
            await ctx.send(embed = embeded)

async def setup(bot):
    await bot.add_cog(Admin(bot))