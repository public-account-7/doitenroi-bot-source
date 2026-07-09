import discord
from discord.ext import commands
from discord import app_commands

import aiohttp
import io
from PIL import Image


class ImageToGif(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="imagetogif",
        description="convert image/url image to gif"
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(
        url="image url",
        image="upload image"
    )
    async def imagetogif(
        self,
        ctx,
        image: discord.Attachment = None,
        url: str = None
    ):

        await ctx.defer()

        target_url = None

        if image:
            target_url = image.url
        elif url:
            target_url = url
        elif ctx.message and ctx.message.attachments:
            target_url = ctx.message.attachments[0].url
        else:
            return await ctx.reply(
                "Please attach an image or provide an image URL."
            )

        async with aiohttp.ClientSession() as session:
            async with session.get(target_url) as resp:

                if resp.status != 200:
                    return await self.bot.sendmessage(ctx,
                        "Failed to download the image."
                    )

                data = io.BytesIO(await resp.read())

        try:
            img = Image.open(data)

            gif_bytes = io.BytesIO()
            img.save(gif_bytes, format="GIF")

            gif_bytes.seek(0)

            await ctx.reply(
                file=discord.File(gif_bytes, filename="converted.gif")
            )

        except Exception as e:
            await self.bot.sendmessage(ctx,f"Error converting image: `{e}`")


async def setup(bot):
    await bot.add_cog(ImageToGif(bot))