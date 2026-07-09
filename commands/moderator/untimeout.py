import discord
from discord.ext import commands


class UnTimeout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="untimeout",
        description="remove timeout from a member."
    )
    @commands.has_permissions(moderate_members=True)
    async def untimeout(
        self,
        ctx,
        member: discord.Member,
        *,
        reason: str = "No reason provided"
    ):

        try:
            await member.timeout(None, reason=reason)

            await self.bot.sendmessage(ctx,
                f"Removed timeout for {member.mention} | Reason: {reason}"
            )

        except Exception as e:
            await self.bot.sendmessage(ctx,f"Failed to remove timeout: {e}")


async def setup(bot):
    await bot.add_cog(UnTimeout(bot))