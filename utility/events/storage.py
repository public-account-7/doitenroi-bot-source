import discord
import os
import secrets

from io import BytesIO


MAX_SIZE = 50 * 1024 * 1024

STORAGE_CHANNEL_ID = os.getenv("STORAGE_SERVER")
STORAGE_GUILD_ID = os.getenv("STORAGE_CHANNEL")


async def get_storage_channel(bot):
    guild = bot.get_guild(
        STORAGE_GUILD_ID
    )

    if not guild:
        return None

    return guild.get_channel(
        STORAGE_CHANNEL_ID
    )


async def save_files(
    bot,
    attachments
):
    try:
        channel = await get_storage_channel(
            bot
        )

        if not channel:
            return [
                f"{a.filename}|URL:"
                for a, _ in attachments
            ]

        files = []
        valid = []

        for attachment, data in attachments:
            filename = (
                attachment.filename
                or "file"
            )

            _, ext = os.path.splitext(
                filename
            )

            random_name = (
                f"{secrets.token_hex(8)}{ext}"
            )

            files.append(
                discord.File(
                    BytesIO(data),
                    filename=random_name
                )
            )

            valid.append(
                attachment
            )

        msg = await channel.send(
            files=files
        )

        results = []

        for i, attachment in enumerate(valid):
            url = msg.attachments[i].url

            results.append(
                f"{attachment.filename}|URL:{url}"
            )

        return results

    except:
        return [
            f"{a.filename}|URL:{a.url}"
            for a, _ in attachments
        ]