import discord
from discord.ext import commands

class lockdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="lockdown", description="lock all channels.")
    @commands.has_permissions(manage_channels=True)
    async def lockdown(self, ctx):

        for channel in ctx.guild.text_channels:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False)

        await self.bot.sendmessage(ctx, "server locked.")

    @commands.hybrid_command(name="unlockdown", description="unlock all channels.")
    @commands.has_permissions(manage_channels=True)
    async def unlockdown(self, ctx):

        for channel in ctx.guild.text_channels:
            await channel.set_permissions(ctx.guild.default_role, send_messages=True)

        await self.bot.sendmessage(ctx, "server unlocked.")


async def setup(bot):
    await bot.add_cog(lockdown(bot))
