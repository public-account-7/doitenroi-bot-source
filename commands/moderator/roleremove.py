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


def resolve_role(ctx, arg: str):
    arg = arg.strip()

    if arg.isdigit():
        return ctx.guild.get_role(int(arg))

    if arg.startswith("<@&") and arg.endswith(">"):
        arg = arg.replace("<@&", "").replace(">", "")
        if arg.isdigit():
            return ctx.guild.get_role(int(arg))

    arg_lower = arg.lower()
    for r in ctx.guild.roles:
        if r.name.lower() == arg_lower:
            return r

    return None


class roleremove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="roleremove",
        description="remove a role from a member."
    )
    @commands.has_permissions(manage_roles=True)
    async def roleremove(self, ctx, member: str, *, role: str):

        member = resolve_member(ctx, member)
        if not member:
            return await self.bot.sendmessage(ctx, "member not found.")

        actual_role = resolve_role(ctx, role)
        if not actual_role:
            return await self.bot.sendmessage(ctx, "role not found.")

        if actual_role.position >= ctx.guild.me.top_role.position:
            return await self.bot.sendmessage(ctx,
                "i can't remove that role (higher than my top role)."
            )

        if member.top_role.position >= ctx.guild.me.top_role.position:
            return await self.bot.sendmessage(ctx,
                "i can't modify this member (they are higher than me)."
            )

        if ctx.author != ctx.guild.owner:

            if actual_role.position >= ctx.author.top_role.position:
                return await self.bot.sendmessage(ctx,
                    "you cannot remove a role equal or higher than your top role."
                )

            if member.top_role.position >= ctx.author.top_role.position:
                return await self.bot.sendmessage(ctx,
                    "you cannot modify this member (they are equal or higher than you)."
                )

        if actual_role not in member.roles:
            return await self.bot.sendmessage(ctx,
                f"{member.mention} does not have that role."
            )

        await member.remove_roles(actual_role)

        await self.bot.sendmessage(ctx,
            f"removed **{actual_role.name}** from {member.mention}."
        )


async def setup(bot):
    await bot.add_cog(roleremove(bot))