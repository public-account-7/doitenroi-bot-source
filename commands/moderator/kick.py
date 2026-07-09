import discord
from discord.ext import commands

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


def can_kick(ctx, member: discord.member):
    if member == ctx.author:
        return False, "you cannot kick yourself."

    if member == ctx.guild.owner:
        return False, "you cannot kick the server owner."

    if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
        return False, "you cannot kick a member with an equal or higher role than yours."

    if member.top_role >= ctx.guild.me.top_role:
        return False, "i cannot kick this member because their role is higher than mine."

    return True, None


class kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="kick",
        description="kick a member from the server."
    )
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: str, *, reason: str = "no reason provided"):

        member = resolve_member(ctx, member)
        if not member:
            return await self.bot.sendmessage(ctx, "member not found.")

        allowed, msg = can_kick(ctx, member)
        if not allowed:
            return await self.bot.sendmessage(ctx, msg)

        await member.kick(reason=reason)

        await self.bot.sendmessage(ctx,
            f"kicked {member.mention} | reason: {reason}"
        )


async def setup(bot):
    await bot.add_cog(kick(bot))
