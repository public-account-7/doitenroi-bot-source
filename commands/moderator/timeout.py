import discord
from discord.ext import commands
from datetime import timedelta
import re

def resolve_member(ctx, arg: str):
    arg = arg.strip()

    if arg.isdigit():
        return ctx.guild.get_member(int(arg))

    if arg.startswith("<@") and arg.endswith(">"):
        arg = arg.replace("<@", "").replace("!", "").replace(">", "")
        if arg.isdigit():
            return ctx.guild.get_member(int(arg))

    arg_lower = arg.lower()
    for m in ctx.guild.members:
        if (
            m.name.lower() == arg_lower
            or (m.nick and m.nick.lower() == arg_lower)
            or f"{m.name.lower()}#{m.discriminator}" == arg_lower
        ):
            return m

    return None


def parse_duration(duration: str):
    matches = re.findall(r"(\d+)(mo|y|d|h|m)", duration.lower())
    if not matches:
        return None

    total = 0

    for value, unit in matches:
        value = int(value)

        if unit == "m":
            total += value
        elif unit == "h":
            total += value * 60
        elif unit == "d":
            total += value * 1440
        elif unit == "mo":
            total += value * 43200
        elif unit == "y":
            total += value * 525600

    return total if total > 0 else None


class timeout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="timeout",
        description="timeout a member with a duration (e.g. 1h, 30m, 1h30m)."
    )
    @commands.has_permissions(moderate_members=True)
    async def timeout(
        self,
        ctx,
        member_arg: str,
        duration: str,
        *,
        reason: str = "no reason provided"
    ):

        member = resolve_member(ctx, member_arg)
        if not member:
            return await self.bot.sendmessage(ctx, "member not found.")

        if member == ctx.author:
            return await self.bot.sendmessage(ctx, "you cannot timeout yourself.")

        if member == ctx.guild.owner:
            return await self.bot.sendmessage(ctx, "you cannot timeout the server owner.")

        if member.top_role.position >= ctx.guild.me.top_role.position:
            return await self.bot.sendmessage(ctx, "i cannot timeout this member (higher than me).")

        if ctx.author != ctx.guild.owner:
            if member.top_role.position >= ctx.author.top_role.position:
                return await self.bot.sendmessage(ctx,
                    "you cannot timeout this member (they are equal or higher than you)."
                )

        minutes = parse_duration(duration)

        if minutes is None:
            return await self.bot.sendmessage(ctx,
                "invalid duration! use format like 10m, 1h, 2d, 1mo, 1y, 1h30m"
            )

        minutes = min(minutes, 40320)

        until = discord.utils.utcnow() + timedelta(minutes=minutes)

        try:
            await member.timeout(until, reason=reason)

            await self.bot.sendmessage(ctx,
                f"timed out {member.mention} for {duration} | reason: {reason}"
            )

        except Exception as e:
            await self.bot.sendmessage(ctx,
                f"failed to timeout {member.mention}: {e}"
            )


async def setup(bot):
    await bot.add_cog(timeout(bot))
