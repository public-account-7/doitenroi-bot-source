import discord
from discord.ext import commands
from discord import app_commands

import aiohttp
import io
import random
import string


class Fetch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="fetch",
        description="fetch raw/content and send back as a file"
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def fetch(self, ctx: commands.Context, url: str):

        await ctx.defer()

        if not (url.startswith("http://") or url.startswith("https://")):
            return await self.bot.sendmessage(ctx,"only accept `http://` or `https://` urls")

        try:
            headers = {
                "Accept": "*/*",
                "Accept-Encoding": "deflate, gzip, zstd",
                "Cache-Control": "no-cache",
                "Requester": "Client",
                "User-Agent": (
                    "Mozilla/5.0 (5591MB; 1080x2112; 397x393; 391x766; Vsmart Live 4; 11) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "ROBLOX Android App 2.703.1353 Phone Hybrid() "
                    "GooglePlayStore RobloxApp/2.703.1353 (GlobalDist; GooglePlayStore) "
                    "Delta 2.0 Velocity Xeno"
                )
            }

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, allow_redirects=True) as response:
                    status = response.status
                    content = await response.read()

            filename = ''.join(
                random.choices(string.ascii_lowercase + string.digits, k=8)
            ) + ".txt"

            file = discord.File(io.BytesIO(content), filename=filename)

            await self.bot.sendmessage(ctx,
                f"status code {status}",
                file=file
            )

        except Exception as e:
            await self.bot.sendmessage(ctx,f"Error: {e}")


async def setup(bot):
    await bot.add_cog(Fetch(bot))