import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json


class RobloxAvatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="robloxavatar",
        description="get avatar roblox player"
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(username="username roblox")
    async def robloxavatar(self, ctx: commands.Context, username: str):

        await ctx.defer()

        async with aiohttp.ClientSession() as session:

            payload = {
                "usernames": [username],
                "excludeBannedUsers": False
            }

            async with session.post(
                "https://users.roblox.com/v1/usernames/users",
                headers={"Content-Type": "application/json"},
                json=payload
            ) as res:

                user_data = await res.json()

            if not user_data.get("data"):
                return await self.bot.sendmessage(ctx,f"not found {username}")

            user_id = user_data["data"][0]["id"]
            username_real = user_data["data"][0]["name"]

            async with session.get(
                f"https://thumbnails.roblox.com/v1/users/avatar"
                f"?userIds={user_id}&size=420x420&format=Png&isCircular=false"
            ) as res:

                avatar_data = await res.json()

            if not avatar_data.get("data"):
                return await self.bot.sendmessage(ctx,
                    f"failed to get avatar for {username_real}"
                )

            avatar_url = avatar_data["data"][0]["imageUrl"]

        await self.bot.sendmessage(ctx,avatar_url)


async def setup(bot):
    await bot.add_cog(RobloxAvatar(bot))