from discord.ext import commands
from discord import app_commands
import discord
import a2s


class CS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="cs-serverinfo",
        description="show counter strike server information"
    )
    @app_commands.allowed_installs(
        guilds=True,
        users=True
    )
    @app_commands.allowed_contexts(
        guilds=True,
        dms=True,
        private_channels=True
    )
    @app_commands.describe(
        address="server ip and port (example: 127.0.0.1:27015)"
    )
    async def serverinfo(
        self,
        ctx,
        address: str
    ):
        if ":" not in address:
            return await self.bot.sendmessage(
                ctx,
                "invalid format. use `ip:port`"
            )

        ip, port = address.split(":", 1)

        try:
            port = int(port)
        except:
            return await self.bot.sendmessage(
                ctx,
                "invalid port"
            )

        if ctx.interaction:
            await ctx.defer()

        try:
            info = await a2s.ainfo(
                (ip, port)
            )

            embed = discord.Embed(
                title="Server Info",
                color=discord.Color.blurple()
            )

            embed.add_field(
                name="Server Name",
                value=info.server_name or "unknown",
                inline=False
            )

            embed.add_field(
                name="Game",
                value=info.game or "unknown",
                inline=True
            )

            embed.add_field(
                name="Map",
                value=info.map_name or "unknown",
                inline=True
            )

            embed.add_field(
                name="Players",
                value=f"{info.player_count}/{info.max_players}",
                inline=True
            )

            embed.add_field(
                name="VAC",
                value="enabled" if info.vac_enabled else "disabled",
                inline=True
            )

            embed.add_field(
                name="Has Password?",
                value="yes" if info.password_protected else "no",
                inline=True
            )

            embed.add_field(
                name="Address",
                value=address,
                inline=False
            )

            await self.bot.sendmessage(
                ctx,
                embed=embed
            )

        except Exception as e:
            await self.bot.sendmessage(
                ctx,
                f"failed to query server: `{e}`"
            )


async def setup(bot):
    await bot.add_cog(CS(bot))