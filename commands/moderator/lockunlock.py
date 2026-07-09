import discord
from discord.ext import commands

class lock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="lock",
        description="lock the current channel."
    )
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    async def lock(self, ctx: commands.context):

        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)

        if overwrite.send_messages is False:
            return await self.bot.sendmessage(ctx, "channel already locked.")

        overwrite.send_messages = False

        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        await self.bot.sendmessage(ctx, f"{ctx.channel.mention} has been locked.")

    @commands.hybrid_command(
        name="unlock",
        description="unlock the current channel."
    )
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    async def unlock(self, ctx: commands.context):

        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)

        if overwrite.send_messages is True:
            return await self.bot.sendmessage(ctx, "channel already unlocked.")

        overwrite.send_messages = True

        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        await self.bot.sendmessage(ctx, f"{ctx.channel.mention} has been unlocked.")


async def setup(bot):
    await bot.add_cog(lock(bot))
