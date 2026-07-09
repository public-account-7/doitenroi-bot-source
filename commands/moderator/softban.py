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


class softban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="softban",
        description="softban a member (ban then immediately unban to delete user messages)."
    )
    @commands.has_permissions(ban_members=True)
    async def softban(self, ctx, member: str, *, reason: str = "no reason provided"):

        member = resolve_member(ctx, member)
        if not member:
            return await self.bot.sendmessage(ctx, "member not found.")

        if member.id == ctx.guild.owner_id:
            return await self.bot.sendmessage(ctx, "you cannot softban the server owner.")

        if member.top_role.position >= ctx.guild.me.top_role.position:
            return await self.bot.sendmessage(ctx, "i cannot softban this member (higher than me).")

        if ctx.author != ctx.guild.owner:
            if member.top_role.position >= ctx.author.top_role.position:
                return await self.bot.sendmessage(ctx,
                    "you cannot softban this member (they are equal or higher than you)."
                )

        await member.ban(reason=reason, delete_message_days=7)
        await ctx.guild.unban(member)

        await self.bot.sendmessage(ctx,
            f"softbanned {member.mention} | reason: {reason}"
        )


async def setup(bot):
    await bot.add_cog(softban(bot))
