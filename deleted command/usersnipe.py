import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import cloudscraper
import random
import string
import asyncio
import io

ROBLOX_CHARS = (
    string.ascii_letters +
    string.digits
)

TIKTOK_CHARS = (
    string.ascii_lowercase +
    string.digits
)

INSTAGRAM_CHARS = (
    string.ascii_lowercase +
    string.digits
)

TIKTOK_HEADERS = [
    {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/91.0.4472.124 "
            "Safari/537.36"
        )
    },
    {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/91.0.4472.114 "
            "Safari/537.36"
        )
    },
    {
        "User-Agent": (
            "Mozilla/5.0 "
            "(X11; Ubuntu; Linux x86_64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/91.0.4472.77 "
            "Safari/537.36"
        )
    }
]


class UserSnipe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.cooldown = commands.CooldownMapping.from_cooldown(
            1,
            60,
            commands.BucketType.user
        )

        self.platforms = {
            "Roblox",
            "TikTok",
            "Instagram"
        }

        self.scraper = cloudscraper.create_scraper()

    def generate_username(
        self,
        length: int,
        platform: str
    ):

        while True:

            if platform == "Roblox":

                username = ''.join(
                    random.choices(
                        ROBLOX_CHARS,
                        k=length
                    )
                )

                if (
                    3 <= len(username) <= 20
                    and not username.startswith("_")
                    and not username.endswith("_")
                    and "__" not in username
                ):
                    return username

            elif platform == "TikTok":

                username = [
                    random.choice(
                        string.ascii_lowercase
                    )
                ]

                separators = 0
                digit_count = 0

                while len(username) < length:

                    prev = username[-1]

                    allowed = (
                        string.ascii_lowercase +
                        string.digits
                    )

                    if (
                        prev not in "._"
                        and separators < 2
                    ):
                        allowed += "._"

                    char = random.choice(allowed)

                    if char in "._":
                        separators += 1

                    if char.isdigit():
                        digit_count += 1

                    username.append(char)

                username = ''.join(username)

                if (
                    not 2 <= len(username) <= 24
                ):
                    continue

                if (
                    username.endswith(".")
                    or username.endswith("_")
                ):
                    continue

                if (
                    ".." in username
                    or "__" in username
                    or "._" in username
                    or "_." in username
                ):
                    continue

                if digit_count > (
                    len(username) // 2
                ):
                    continue

                vowels = "aeiou"

                vowel_count = sum(
                    1 for c in username
                    if c in vowels
                )

                if vowel_count == 0:
                    continue

                return username.lower()

            elif platform == "Instagram":

                username = [
                    random.choice(
                        string.ascii_lowercase
                    )
                ]

                separators = 0
                digit_count = 0

                while len(username) < length:

                    prev = username[-1]

                    allowed = (
                        string.ascii_lowercase +
                        string.digits
                    )

                    if (
                        prev not in "._"
                        and separators < 2
                    ):
                        allowed += "._"

                    char = random.choice(allowed)

                    if char in "._":
                        separators += 1

                    if char.isdigit():
                        digit_count += 1

                    username.append(char)

                username = ''.join(username)

                if (
                    not 1 <= len(username) <= 30
                ):
                    continue

                if (
                    username.endswith(".")
                    or username.endswith("_")
                ):
                    continue

                if (
                    ".." in username
                    or "__" in username
                    or "._" in username
                    or "_." in username
                ):
                    continue

                if digit_count > (
                    len(username) // 2
                ):
                    continue

                vowels = "aeiou"

                vowel_count = sum(
                    1 for c in username
                    if c in vowels
                )

                if vowel_count == 0:
                    continue

                return username.lower()

    async def check_username(
        self,
        session,
        username: str,
        platform: str
    ):
        try:

            if platform == "Roblox":

                async with session.get(
                    "https://auth.roblox.com/v1/usernames/validate",
                    params={
                        "username": username,
                        "birthday": "2000-01-01T00:00:00.000Z",
                        "context": "Signup"
                    },
                    timeout=5
                ) as res:

                    if res.status != 200:
                        return None

                    data = await res.json()

                    if (
                        data.get("code") == 0
                        or "valid" in str(
                            data.get("message", "")
                        ).lower()
                    ):
                        return username

                    return None

            elif platform == "TikTok":

                response = await asyncio.to_thread(
                    self.scraper.get,
                    f"https://www.tiktok.com/@{username}",
                    headers=random.choice(
                        TIKTOK_HEADERS
                    )
                )

                while len(response.text) < 200000:

                    response = await asyncio.to_thread(
                        self.scraper.get,
                        f"https://www.tiktok.com/@{username}",
                        headers=random.choice(
                            TIKTOK_HEADERS
                        )
                    )

                if response.status_code == 200:

                    text = response.text.lower()

                    if (
                        "followingcount"
                        not in text
                        and "followercount"
                        not in text
                        and '"uniqueid":"' not in text
                    ):
                        return username

                return None

            elif platform == "Instagram":

                async with session.get(
                    f"https://www.instagram.com/{username}",
                    timeout=10
                ) as response:

                    content = (
                        await response.text()
                    ).lower()

                    if username.lower() in content:

                        place = content.find(
                            username.lower()
                        )

                        find = content[
                            place - 9:
                            place + 10
                        ]

                        status = (
                            "free"
                            if find[1:4] == "url"
                            else "taken"
                        )

                        if status == "free":
                            return username

                    return None

            return None

        except:
            return None

    def random_filename(self, length=7):
        return (
            ''.join(
                random.choices(
                    string.ascii_letters +
                    string.digits,
                    k=length
                )
            ) + ".txt"
        )

    @commands.hybrid_command(
        name="usersnipe",
        description="check available usernames"
    )
    @app_commands.describe(
        platform="platform to check usernames on",
        letter="username length",
        amount="how many available usernames to find"
    )
    @app_commands.choices(
        platform=[
            app_commands.Choice(
                name="Roblox",
                value="Roblox"
            ),
            app_commands.Choice(
                name="TikTok",
                value="TikTok"
            ),
            app_commands.Choice(
                name="Instagram",
                value="Instagram"
            )
        ]
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
    async def usersnipe(
        self,
        ctx: commands.Context,
        platform: str = "Roblox",
        letter: int = 5,
        amount: int = 5
    ):

        await ctx.defer()

        bucket = self.cooldown.get_bucket(
            ctx.message or ctx.interaction
        )

        retry_after = bucket.update_rate_limit()

        if retry_after:
            return await ctx.send(
                f"slow down, try again in {int(retry_after)}s"
            )

        if platform == "Roblox":

            if letter < 3 or letter > 20:
                return await ctx.send(
                    "roblox username length must be 3-20"
                )

            if amount < 1 or amount > 1000:
                return await ctx.send(
                    "roblox amount must be 1-1000"
                )

        elif platform == "TikTok":

            if letter < 2 or letter > 24:
                return await ctx.send(
                    "tiktok username length must be 2-24"
                )

            if amount < 1 or amount > 100:
                return await ctx.send(
                    "tiktok amount must be 1-100"
                )

        elif platform == "Instagram":

            if letter < 1 or letter > 30:
                return await ctx.send(
                    "instagram username length must be 1-30"
                )

            if amount < 1 or amount > 200:
                return await ctx.send(
                    "instagram amount must be 1-200"
                )

        if platform not in self.platforms:
            return await ctx.send(
                "invalid platform"
            )

        found = []
        found_set = set()

        generated = set()

        total_checked = 0

        stop_event = asyncio.Event()

        lock = asyncio.Lock()

        last_found_time = (
            asyncio.get_event_loop().time()
        )

        async with aiohttp.ClientSession(
            headers={
                "Accept": "*/*",
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/124.0.0.0 "
                    "Safari/537.36"
                )
            }
        ) as session:

            async def worker():
                nonlocal total_checked, last_found_time

                while not stop_event.is_set():

                    while True:

                        username = self.generate_username(
                            letter,
                            platform
                        )

                        async with lock:

                            if username not in generated:
                                generated.add(username)
                                break

                    result = await self.check_username(
                        session,
                        username,
                        platform
                    )

                    total_checked += 1

                    if result:

                        async with lock:

                            if result not in found_set:

                                found_set.add(result)

                                found.append(result)

                                last_found_time = (
                                    asyncio.get_event_loop().time()
                                )

                        if len(found) >= amount:
                            stop_event.set()
                            return

            tasks = [
                asyncio.create_task(worker())
                for _ in range(13)
            ]

            timeout = 30

            try:
                while not stop_event.is_set():

                    now = (
                        asyncio.get_event_loop().time()
                    )

                    if (
                        now - last_found_time
                        >= timeout
                    ):
                        stop_event.set()
                        break

                    await asyncio.sleep(0.05)

            finally:

                stop_event.set()

                for t in tasks:
                    t.cancel()

                await asyncio.gather(
                    *tasks,
                    return_exceptions=True
                )

        if found:

            content = "\n".join(found)

            file = discord.File(
                fp=io.BytesIO(
                    content.encode("utf-8")
                ),
                filename=self.random_filename(7)
            )

            await ctx.send(
                content=(
                    f"found {len(found)}/{amount} "
                    f"available username on {platform} "
                    f"({total_checked} checked)"
                ),
                file=file
            )

        else:

            await ctx.send(
                f"failed to get available username on {platform} "
                f"({total_checked} username checked)"
            )


async def setup(bot):
    await bot.add_cog(UserSnipe(bot))