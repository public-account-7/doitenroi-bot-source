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


class ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="ban",
        description="ban a member from the server."
    )
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: str, *, reason: str = "no reason provided"):

        member = resolve_member(ctx, member)
        if not member:
            return await self.bot.sendmessage(ctx, "member not found.")

        if member == ctx.author:
            return await self.bot.sendmessage(ctx, "you cannot ban yourself.")

        if member == ctx.guild.owner:
            return await self.bot.sendmessage(ctx, "you cannot ban the server owner.")

        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await self.bot.sendmessage(ctx, "you cannot ban this member.")

        if member.top_role >= ctx.guild.me.top_role:
            return await self.bot.sendmessage(ctx, "i cannot ban this member.")

        await member.ban(reason=reason)

        await self.bot.sendmessage(ctx,
            f"banned {member.mention} | reason: {reason}"
        )


async def setup(bot):
    await bot.add_cog(ban(bot))
