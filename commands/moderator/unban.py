import discord
from discord.ext import commands

class unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="unban",
        description="unban a user by id or mention."
    )
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: commands.context, user_arg: str):

        user_arg = user_arg.strip()

        if user_arg.startswith("<@") and user_arg.endswith(">"):
            user_arg = user_arg.replace("<@", "").replace("!", "").replace(">", "")

        if not user_arg.isdigit():
            return await self.bot.sendmessage(ctx, "invalid user.")

        user_id = int(user_arg)

        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)

            await self.bot.sendmessage(ctx, f"unbanned {user.mention}")

        except discord.notfound:
            await self.bot.sendmessage(ctx, "user not found.")

        except discord.forbidden:
            await self.bot.sendmessage(ctx, "i don't have permission to unban this user.")

        except Exception as e:
            await self.bot.sendmessage(ctx, f"failed to unban user: {e}")


async def setup(bot):
    await bot.add_cog(unban(bot))
