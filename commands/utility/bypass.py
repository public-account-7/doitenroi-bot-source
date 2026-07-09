import discord
from discord.ext import commands
from discord import app_commands

import aiohttp
import asyncio
import urllib.parse
import json


bypass_cooldown = commands.CooldownMapping.from_cooldown(
    1, 15, commands.BucketType.user
)


class Bypass(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="bypass",
        description="bypass short link"
    )
    @app_commands.describe(
        url="link to bypass",
        no_cache="fresh bypass (use for workink, linkvertise, etc)",
        api="api bypass"
    )
    @app_commands.choices(no_cache=[
        app_commands.Choice(name="false", value="false"),
        app_commands.Choice(name="true", value="true")
    ])
    @app_commands.choices(api=[
        app_commands.Choice(name="izen.lol", value="izen"),
        app_commands.Choice(name="bypasscity", value="bypasscity")
    ])
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def bypass(self, ctx, url: str, no_cache: str = "false", api: str = "izen"):

        await ctx.defer()

        bucket = bypass_cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()

        if retry_after:
            hours = int(retry_after // 3600)
            minutes = int((retry_after % 3600) // 60)
            seconds = int(retry_after % 60)

            return await self.bot.sendmessage(ctx,
                f"You are on cooldown. Try again in "
                f"{hours} hours, {minutes} minutes, {seconds} seconds.",
                ephemeral=True
            )

        if not (url.startswith("http://") or url.startswith("https://")):
            return await self.bot.sendmessage(ctx,
                "Error: URL must start with http:// or https://"
            )

        encoded = urllib.parse.quote_plus(url)

        if api == "bypasscity":
            base = (
                "http://94.249.197.222:8748/api/freebypass?nocache=true&provider=bypasscity&url="
                if no_cache == "true"
                else "http://94.249.197.222:8748/api/freebypass?provider=bypasscity&url="
            )
        else:
            base = (
                "http://94.249.197.222:8748/api/freebypass?nocache=true&provider=izen&url="
                if no_cache == "true"
                else "http://94.249.197.222:8748/api/freebypass?provider=izen&url="
            )

        full_url = base + encoded
        timeout = aiohttp.ClientTimeout(total=200)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    full_url
                ) as resp:

                    try:
                        data = await resp.json()
                    except Exception:
                        return await self.bot.sendmessage(
                            ctx,
                            f"```text\n{text}\n```"
                        )

                    if data.get("status") == "success" and data.get("result"):
                        await self.bot.sendmessage(ctx, data["result"])
                    else:
                        await self.bot.sendmessage(
                            ctx,
                            f"```json\n{response}\n```"
                        )

        except asyncio.TimeoutError:
            await self.bot.sendmessage(ctx, "Error: API request timed out.")
        except Exception as e:
            await self.bot.sendmessage(
                ctx,
                f"```text\n{str(e).replace(api_key, 'abc')}\n```"
            )


async def setup(bot):
    await bot.add_cog(Bypass(bot))
