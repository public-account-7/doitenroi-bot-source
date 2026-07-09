import discord
from discord.ext import commands
from discord import app_commands

import os
import difflib
import io
import random
import string


STORAGE_DIR = "./storage"


# helper: get all files in storage
def get_storage_files():
    storage_folder = os.path.abspath(STORAGE_DIR)

    if not os.path.isdir(storage_folder):
        return None, None

    files = [
        f for f in os.listdir(storage_folder)
        if os.path.isfile(os.path.join(storage_folder, f))
    ]

    return storage_folder, files


# helper: resolve best matching filename
def resolve_filename(query, files):
    query = query.strip().lower()

    display_map = {}
    display_names = []

    for f in files:
        base = os.path.splitext(f)[0].lower()
        display_map.setdefault(base, []).append(f)
        display_names.append(base)

    # exact match
    if query in display_map:
        return display_map[query][0]

    # substring match
    substr_matches = [base for base in display_names if query in base]
    if substr_matches:
        best = sorted(substr_matches, key=lambda s: (len(s), s))[0]
        return display_map[best][0]

    # fuzzy match
    close = difflib.get_close_matches(query, display_names, n=1, cutoff=0.6)
    if close:
        return display_map[close[0]][0]

    return None


# helper: random filename for sending
def generate_random_filename():
    suffix = ''.join(
        random.choices(string.ascii_letters + string.digits, k=8)
    )
    return f"{suffix}.txt"


class GetFile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="getfile",
        description="get file from storage"
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def getfile(self, ctx: commands.Context, *, name: str):

        storage_folder, files = get_storage_files()

        if storage_folder is None:
            return await self.bot.sendmessage(ctx,"Storage folder not found.")

        if not files:
            return await self.bot.sendmessage(ctx,"No files in storage.")

        matched_filename = resolve_filename(name, files)

        if matched_filename is None:
            return await self.bot.sendmessage(ctx,f"file `{name}` not found in storage.")

        requested = os.path.normpath(
            os.path.join(storage_folder, matched_filename)
        )

        if not os.path.commonpath([storage_folder, requested]) == storage_folder:
            return await self.bot.sendmessage(ctx,"Invalid file path.")

        with open(requested, "rb") as f:
            file_bytes = f.read()

        file_like = io.BytesIO(file_bytes)
        file_like.seek(0)

        send_file_name = generate_random_filename()

        discord_file = discord.File(
            fp=file_like,
            filename=send_file_name
        )

        await self.bot.sendmessage(ctx,
            f"sended file `{matched_filename}`",
            file=discord_file
        )


async def setup(bot):
    await bot.add_cog(GetFile(bot))