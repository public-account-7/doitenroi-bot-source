import discord
from discord.ext import commands
from discord import app_commands
import time
import platform


class InfoBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="infobot",
        description="Show bot statistics"
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def infobot(self, ctx: commands.Context):

        uptime_seconds = int(time.time() - self.bot.start_time)

        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        uptime = f"{days}d {hours}h {minutes}m {seconds}s"

        total_guilds = len(self.bot.guilds)
        total_members = sum(
            guild.member_count or 0
            for guild in self.bot.guilds
        )

        embed = discord.Embed(
            title=f"{self.bot.user.name} Info",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="Servers",
            value=f"{total_guilds:,}",
            inline=True
        )

        embed.add_field(
            name="Members",
            value=f"{total_members:,}",
            inline=True
        )

        embed.add_field(
            name="Uptime",
            value=uptime,
            inline=True
        )

        embed.add_field(
            name="Python Version",
            value=platform.python_version(),
            inline=True
        )

        embed.add_field(
            name="Discord.py Version",
            value=discord.__version__,
            inline=True
        )

        await self.bot.sendmessage(ctx, embed=embed)


async def setup(bot):
    await bot.add_cog(InfoBot(bot))