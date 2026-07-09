import asyncio
import aiohttp
import hashlib
import random

from io import BytesIO
from PIL import (
    Image,
    ImageEnhance,
    ImageFilter
)


OCR_API_URL = "https://api.ocr.space/parse/image"

OCR_API_KEYS = os.getenv("OCR_APIKEY")


class ScamDetector:
    def __init__(self, bot):
        self.bot = bot

        self.http = aiohttp.ClientSession()

        self.queue = asyncio.Queue(
            maxsize=200
        )

        self.scan_rate = 5
        self.scan_tokens = self.scan_rate
        self.last_refill = (
            asyncio.get_event_loop().time()
        )

        self.hash_cache = {}

        self.scam_hashes = (
            self.get_scam_hashes()
        )

        self.bot.loop.create_task(
            self.worker()
        )

    async def close(self):
        await self.http.close()

    async def acquire_token(self):
        now = asyncio.get_event_loop().time()

        elapsed = (
            now - self.last_refill
        )

        refill = int(
            elapsed * self.scan_rate
        )

        if refill > 0:
            self.scan_tokens = min(
                self.scan_tokens + refill,
                self.scan_rate
            )

            self.last_refill = now

        while self.scan_tokens <= 0:
            await asyncio.sleep(0.1)

            return await self.acquire_token()

        self.scan_tokens -= 1

    async def worker(self):
        while True:
            message, image = await self.queue.get()

            try:
                await self.acquire_token()

                if await self.is_scam(image):
                    try:
                        me = message.guild.me

                        if (
                            not me.guild_permissions.ban_members
                            or message.author == message.guild.owner
                        ):
                            continue

                        try:
                            await message.author.send(
                                f"[{message.guild.name}] Softbanned due to crypto scam, u can join back server again using a server invite."
                            )
                        except:
                            pass

                        try:
                            await message.guild.ban(
                                message.author,
                                delete_message_days=1,
                                reason="crypto scam"
                            )

                            await message.guild.unban(
                                message.author,
                                reason="crypto scam"
                            )
                        except:
                            pass

                    except:
                        pass

            finally:
                self.queue.task_done()

    def compress_image(
        self,
        image_bytes
    ):
        try:
            img = Image.open(
                BytesIO(image_bytes)
            ).convert("L")

            if img.width < 800:
                scale = 800 / img.width

                img = img.resize(
                    (
                        int(img.width * scale),
                        int(img.height * scale)
                    )
                )

            img.thumbnail((1600, 1600))

            img = (
                ImageEnhance.Contrast(img)
                .enhance(2.0)
            )

            img = img.filter(
                ImageFilter.SHARPEN
            )

            img = img.point(
                lambda x:
                0 if x < 140 else 255
            )

            buffer = BytesIO()

            img.save(
                buffer,
                format="JPEG",
                quality=85,
                optimize=True
            )

            return buffer.getvalue()

        except:
            return image_bytes

    def get_hash(
        self,
        image_bytes
    ):
        try:
            img = Image.open(
                BytesIO(image_bytes)
            ).convert("RGB")

            img.thumbnail(
                (512, 512)
            )

            buffer = BytesIO()

            img.save(
                buffer,
                format="JPEG",
                quality=60
            )

            return hashlib.sha256(
                buffer.getvalue()
            ).hexdigest()

        except:
            return hashlib.sha256(
                image_bytes
            ).hexdigest()

    def get_scam_hashes(self):
        try:
            data = self.bot.load_data()

            return set(
                data.get(
                    "cachescamhash",
                    []
                )
            )

        except:
            return set()

    def add_scam_hash(
        self,
        img_hash
    ):
        try:
            data = self.bot.load_data()

            hashes = data.setdefault(
                "cachescamhash",
                []
            )

            if img_hash not in hashes:
                hashes.append(img_hash)

                self.bot.save_data(
                    data
                )

        except:
            pass

    async def ocr(
        self,
        image_bytes
    ):
        try:
            if len(image_bytes) > (
                1 * 1024 * 1024
            ):
                image_bytes = (
                    self.compress_image(
                        image_bytes
                    )
                )

            form = aiohttp.FormData()

            form.add_field(
                "apikey",
                random.choice(
                    OCR_API_KEYS
                )
            )

            form.add_field(
                "language",
                "eng"
            )

            form.add_field(
                "isOverlayRequired",
                "false"
            )

            form.add_field(
                "file",
                image_bytes,
                filename="image.jpg"
            )

            async with self.http.post(
                OCR_API_URL,
                data=form
            ) as resp:
                data = await resp.json()

            if data.get(
                "IsErroredOnProcessing"
            ):
                return ""

            parsed = data.get(
                "ParsedResults",
                []
            )

            if not parsed:
                return ""

            return (
                parsed[0]
                .get(
                    "ParsedText",
                    ""
                )
                .lower()
                .strip()
            )

        except:
            return ""

    async def is_scam(
        self,
        image_bytes
    ):
        try:
            h = self.get_hash(
                image_bytes
            )

            if h in self.hash_cache:
                return self.hash_cache[h]

            self.scam_hashes = (
                self.get_scam_hashes()
            )

            if h in self.scam_hashes:
                self.hash_cache[h] = True

                return True

            text = await self.ocr(
                image_bytes
            )

            keywords = [
                "withdrawal success",
                "successfull withdraw",
                "receive usdt",
                "activate your voucher",
                "withdrawal successful",
                "usdt",
                "crypto",
                "bonus",
                "claim now",
                "instant withdrawal",
                "your withdrawal of",
                "the money will be transferred to",
                "credited",
                "payment received",
                "transaction successful",
                "activate code for bonus",
                "special promo code",
                "withdraw the bonus"
            ]

            found = [
                kw
                for kw in keywords
                if kw in text
            ]

            score = len(found)

            result = score >= 2

            if result:
                self.add_scam_hash(h)

                self.scam_hashes.add(h)

            self.hash_cache[h] = result

            return result

        except:
            return False