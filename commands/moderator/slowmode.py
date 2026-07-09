import discord
from discord.ext import commands
import re

def parse_duration(duration: str):
    matches = re.findall(r"(\d+)(s|m|h)", duration.lower())
    if not matches:
        return None

    total = 0

    for value, unit in matches:
        value = int(value)

        if unit == "s":
            total += value
        elif unit == "m":
            total += value * 60
        elif unit == "h":
            total += value * 3600

    return total if total > 0 else None


class slowmode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="slowmode", description="set channel slowmode (e.g. 10s, 5m, 1h, 1h30m).")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, duration: str):

        seconds = parse_duration(duration)

        if seconds is None:
            return await self.bot.sendmessage(ctx, "invalid format. use 10s, 5m, 1h, 1h30m.")

        if seconds > 21600:
            seconds = 21600

        await ctx.channel.edit(slowmode_delay=seconds)

        await self.bot.sendmessage(ctx, f"slowmode set to {duration}.")


async def setup(bot):
    await bot.add_cog(slowmode(bot))
