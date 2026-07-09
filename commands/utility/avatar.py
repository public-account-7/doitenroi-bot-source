import discord
from discord.ext import commands
from discord import app_commands


class Avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="avatar",
        description="get user avatar"
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(user="user to get avatar (optional)")
    async def avatar(
        self,
        ctx: commands.Context,
        user: discord.Member | discord.User | None = None
    ):
        user = user or ctx.author
        await self.bot.sendmessage(ctx, user.display_avatar.url)


async def setup(bot):
    await bot.add_cog(Avatar(bot))