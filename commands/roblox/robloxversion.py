import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
from google_play_scraper import app as gp_app
from datetime import datetime, timezone

WEAO_API = "https://weao.xyz/api/versions/current"
USER_AGENT = "WEAO-3PService"

ROBLOX_CLIENT_SETTINGS = "https://clientsettings.roblox.com/v2/client-version/WindowsPlayer"
ROBLOX_CLIENT_SETTINGS_MAC = "https://clientsettings.roblox.com/v2/client-version/MacPlayer"

ROBLOX_ANDROID_GLOBAL = "com.roblox.client"
ROBLOX_ANDROID_VNG = "com.roblox.client.vnggames"
ROBLOX_IOS_GLOBAL = "431946152"
ROBLOX_IOS_VNG = "6474715805"


class RobloxVersion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        await self.session.close()

    async def fetch_weao(self):
        headers = {"User-Agent": USER_AGENT}
        for i in range(3):
            try:
                async with self.session.get(WEAO_API, headers=headers) as resp:
                    if resp.status == 200:
                        return await resp.json(content_type=None)
                    if resp.status == 429:
                        await asyncio.sleep(2 * (i + 1))
            except:
                await asyncio.sleep(1)
        return None

    async def fetch_json(self, url):
        try:
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json(content_type=None)
        except:
            pass
        return None

    async def fetch_ios(self, app_id, country):
        url = f"https://itunes.apple.com/lookup?id={app_id}&country={country}&_={asyncio.get_event_loop().time()}"

        headers = {
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": "Mozilla/5.0"
        }

        for i in range(3):
            try:
                async with self.session.get(url, headers=headers) as resp:
                    if resp.status == 429:
                        await asyncio.sleep(2 * (i + 1))
                        continue
                    if resp.status != 200:
                        await asyncio.sleep(1)
                        continue

                    data = await resp.json(content_type=None)

                    if not data.get("results"):
                        await asyncio.sleep(1)
                        continue

                    app = data["results"][0]
                    return app.get("version", "Unknown"), app.get("currentVersionReleaseDate", "Unknown")

            except:
                await asyncio.sleep(1)

        return None

    async def fetch_android(self, app_id):
        try:
            return await self.bot.loop.run_in_executor(None, lambda: gp_app(app_id))
        except:
            return None

    @commands.hybrid_command(name="robloxversion", description="show latest version of roblox")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def robloxversion(self, ctx: commands.Context):

        weao_data, win_data, mac_data, ios_global, ios_vng, android_global, android_vng = await asyncio.gather(
            self.fetch_weao(),
            self.fetch_json(ROBLOX_CLIENT_SETTINGS),
            self.fetch_json(ROBLOX_CLIENT_SETTINGS_MAC),
            self.fetch_ios(ROBLOX_IOS_GLOBAL, "us"),
            self.fetch_ios(ROBLOX_IOS_VNG, "vn"),
            self.fetch_android(ROBLOX_ANDROID_GLOBAL),
            self.fetch_android(ROBLOX_ANDROID_VNG),
        )

        def to_ts(ts):
            try:
                return f"<t:{int(ts)}:R>"
            except:
                return "Unknown"

        def parse_date(v):
            if not v:
                return "Unknown"
            try:
                return to_ts(int(v))
            except:
                pass
            try:
                dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
                return to_ts(int(dt.timestamp()))
            except:
                pass
            try:
                dt = datetime.strptime(v, "%m/%d/%Y, %I:%M:%S %p %Z")
                dt = dt.replace(tzinfo=timezone.utc)
                return to_ts(int(dt.timestamp()))
            except:
                pass
            return "Unknown"

        def parse_client(d):
            if not d:
                return "Error"
            return d.get("clientVersionUpload", "Unknown")

        def parse_android(d):
            if not d:
                return "Error", "Error"
            return d.get("version", "Unknown"), to_ts(d.get("updated"))

        def parse_ios(d):
            if not d:
                return "Error", "Error"
            v, t = d
            return v, parse_date(t)

        win_cur = parse_client(win_data)
        mac_cur = parse_client(mac_data)

        android_global_v, android_global_t = parse_android(android_global)
        android_vng_v, android_vng_t = parse_android(android_vng)

        ios_global_v, ios_global_t = parse_ios(ios_global)
        ios_vng_v, ios_vng_t = parse_ios(ios_vng)

        if weao_data:
            win_text = f"**Version:** {weao_data.get('Windows','Unknown')}\n**Last Updated:** {parse_date(weao_data.get('WindowsDate'))}"
            mac_text = f"**Version:** {weao_data.get('Mac','Unknown')}\n**Last Updated:** {parse_date(weao_data.get('MacDate'))}"
        else:
            win_text = f"**Version:** {win_cur}"
            mac_text = f"**Version:** {mac_cur}"

        embed = discord.Embed(title="Latest Roblox Versions", color=discord.Color.green())

        embed.add_field(name="Windows", value=win_text, inline=False)
        embed.add_field(name="Mac", value=mac_text, inline=False)

        embed.add_field(
            name="Android",
            value=f"**Global:** {android_global_v} ({android_global_t})\n**VNG:** {android_vng_v} ({android_vng_t})",
            inline=False
        )

        embed.add_field(
            name="iOS",
            value=f"**Global:** {ios_global_v} ({ios_global_t})\n**VNG:** {ios_vng_v} ({ios_vng_t})",
            inline=False
        )

        await self.bot.sendmessage(ctx, embed=embed)


async def setup(bot):
    await bot.add_cog(RobloxVersion(bot))