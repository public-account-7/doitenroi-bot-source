import discord
from discord.ext import commands


class ClearSnipes(commands.Cog):
    def __init__(
        self,
        bot
    ):
        self.bot = bot

    @commands.hybrid_command(
        name="clearsnipes",
        description="clear all snipe data in this server"
    )
    @commands.has_permissions(
        manage_messages=True
    )
    async def clearsnipes(
        self,
        ctx
    ):
        if not ctx.guild:
            return await ctx.send(
                "server only"
            )

        guilds = (
            self.bot.load_data()
            .setdefault(
                "guilds",
                {}
            )
        )

        guild_data = guilds.setdefault(
            str(ctx.guild.id),
            {}
        )

        snipes = guild_data.get(
            "snipes",
            []
        )

        if not snipes:
            return await ctx.send(
                "no snipe data found"
            )

        amount = len(snipes)

        guild_data["snipes"] = []

        await self.bot.save_data()

        await ctx.send(
            f"cleared `{amount}` snipe entries"
        )


async def setup(bot):
    await bot.add_cog(
        ClearSnipes(bot)
    )