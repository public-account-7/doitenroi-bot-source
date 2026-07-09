import discord
from discord.ext import commands
from discord import app_commands


class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="ping", description="Check bot latency")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(title="Ping", color=discord.Color.blurple())
        embed.add_field(name="Latency", value=f"{latency} ms", inline=True)
        await self.bot.sendmessage(ctx, embed=embed)


async def setup(bot):
    await bot.add_cog(Ping(bot))