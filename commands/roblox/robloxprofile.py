import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
from datetime import datetime, timezone

def discord_time(dt: datetime):
    ts = int(dt.timestamp())
    return f"<t:{ts}:F> • <t:{ts}:R>"

def parse_created(created_str):
    if not created_str:
        return None, "Unknown"
    try:
        dt = datetime.strptime(created_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        return dt, discord_time(dt)
    except:
        return None, "Unknown"

def limit_text(text, max_len=300):
    if not text:
        return None
    return text[:max_len] + ("..." if len(text) > max_len else "")

async def fetch_json(session, method, url, **kwargs):
    for _ in range(3):
        async with session.request(method, url, **kwargs) as res:
            if res.status == 429:
                retry = res.headers.get("Retry-After")
                wait = float(retry) if retry else 1.5
                await asyncio.sleep(wait)
                continue
            try:
                return await res.json()
            except:
                return None
    return None

class RobloxProfile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive"
        }

    async def cog_load(self):
        self.session = aiohttp.ClientSession(headers=self.headers)

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    @commands.hybrid_command(name="robloxprofile", description="Get Roblox profile info")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(username="Roblox username")
    async def robloxprofile(self, ctx, username: str):
        await ctx.defer()

        data = await fetch_json(
            self.session,
            "POST",
            "https://users.roblox.com/v1/usernames/users",
            json={"usernames": [username]}
        )

        if not data or not data.get("data"):
            return await self.bot.sendmessage(ctx, f"User not found: {username}")

        user = data["data"][0]
        user_id = user["id"]
        username_real = user["name"]

        tasks = await asyncio.gather(
            fetch_json(self.session, "GET", f"https://users.roblox.com/v1/users/{user_id}"),
            fetch_json(self.session, "GET", f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png"),
            fetch_json(self.session, "POST", "https://presence.roblox.com/v1/presence/users", json={"userIds": [user_id]}),
            fetch_json(self.session, "GET", f"https://friends.roblox.com/v1/users/{user_id}/followers/count"),
            fetch_json(self.session, "GET", f"https://friends.roblox.com/v1/users/{user_id}/followings/count"),
            fetch_json(self.session, "GET", f"https://friends.roblox.com/v1/users/{user_id}/friends/count"),
            fetch_json(self.session, "GET", f"https://users.roblox.com/v1/users/{user_id}/username-history?limit=100"),
            fetch_json(self.session, "GET", f"https://api.rolimons.com/players/v1/playerassets/{user_id}")
        )

        profile, avatar_data, presence_data, followers_data, following_data, friends_data, history, roli = tasks

        avatar = None
        if avatar_data and avatar_data.get("data"):
            avatar = avatar_data["data"][0]["imageUrl"]

        presence = (presence_data or {}).get("userPresences", [{}])[0]
        ptype = presence.get("userPresenceType", 0)

        followers = followers_data.get("count") if followers_data else None
        following = following_data.get("count") if following_data else None
        friends = friends_data.get("count") if friends_data else None

        past_names = None
        if history:
            names = [entry["name"] for entry in history.get("data", []) if entry.get("name")]
            if names:
                past_names = ", ".join(names[:10])
                if len(names) > 10:
                    past_names += f" (+{len(names) - 10} more)"

        premium_value = None
        last_location = None
        if roli and roli.get("success"):
            premium_value = "✔" if roli.get("premium") else "✖"
            loc = roli.get("lastLocation")
            if loc:
                last_location = loc

        display = profile.get("displayName", username_real) if profile else username_real
        description = limit_text(profile.get("description") if profile else None)

        created_dt, created_display = parse_created(profile.get("created") if profile else None)

        age_days = "Unknown"
        if created_dt:
            age_days = f"{(datetime.now(timezone.utc) - created_dt).days} days"

        verified = "✔" if profile and profile.get("hasVerifiedBadge") else "✖"
        banned = "✔" if profile and profile.get("isBanned") else "✖"

        status = (
            "Online" if ptype == 2
            else "In Game" if ptype == 3
            else "Offline"
        )

        profile_url = f"https://www.roblox.com/users/{user_id}/profile"

        embed = discord.Embed(
            title=f"{display} (@{username_real})",
            url=profile_url,
            color=discord.Color.blurple()
        )

        if avatar:
            embed.set_thumbnail(url=avatar)

        embed.add_field(name="ID", value=user_id, inline=True)
        embed.add_field(name="Verified", value=verified, inline=True)
        embed.add_field(name="Banned", value=banned, inline=True)

        embed.add_field(name="Status", value=status, inline=True)
        embed.add_field(name="Account Age", value=age_days, inline=True)

        if followers is not None:
            embed.add_field(name="Followers", value=f"{followers:,}", inline=True)

        if following is not None:
            embed.add_field(name="Following", value=f"{following:,}", inline=True)

        if friends is not None:
            embed.add_field(name="Friends", value=f"{friends:,}", inline=True)

        if premium_value is not None:
            embed.add_field(name="Premium", value=premium_value, inline=True)

        if last_location is not None:
            embed.add_field(name="Last Location", value=last_location, inline=True)

        embed.add_field(name="Created", value=created_display, inline=False)

        if past_names:
            embed.add_field(name="Past Names", value=past_names, inline=False)

        if description:
            embed.add_field(name="Description", value=description, inline=False)

        await self.bot.sendmessage(ctx, embed=embed)

async def setup(bot):
    await bot.add_cog(RobloxProfile(bot))
