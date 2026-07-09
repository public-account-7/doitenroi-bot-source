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
        if m.name.lower() == arg_lower or (m.nick and m.nick.lower() == arg_lower):
            return m

    return None


class nickname(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="setnick", description="change user nickname.")
    @commands.has_permissions(manage_nicknames=True)
    async def nick(self, ctx, member: str, *, name: str = None):

        member = resolve_member(ctx, member)
        if not member:
            return await self.bot.sendmessage(ctx, "member not found.")

        if member.top_role >= ctx.guild.me.top_role:
            return await self.bot.sendmessage(ctx, "i cannot edit this member.")

        if ctx.author != ctx.guild.owner:
            if member.top_role >= ctx.author.top_role:
                return await self.bot.sendmessage(ctx, "you cannot edit this member.")

        await member.edit(nick=name)

        await self.bot.sendmessage(ctx, f"nickname updated for {member.mention}.")


async def setup(bot):
    await bot.add_cog(nickname(bot))
