import sys
sys.dont_write_bytecode = True

import os
import json
import time
import orjson
import asyncio
import logging
from pathlib import Path

import discord
from dotenv import load_dotenv
from discord.ext import commands

logging.getLogger("wavelink").setLevel(logging.CRITICAL)
logging.getLogger("wavelink.node").setLevel(logging.CRITICAL)
logging.getLogger("wavelink.pool").setLevel(logging.CRITICAL)
logging.getLogger("websockets").setLevel(logging.CRITICAL)
logging.getLogger("aiohttp").setLevel(logging.CRITICAL)

load_dotenv()

TOKEN = os.getenv("TOKEN")

DATA_FILE = "data.json"

DEFAULT_PREFIX = "+"

IGNORED_FOLDERS = {
    "__pycache__",
    ".git",
    "backup",
    "backups"
}

def warn(msg):
    print(f"[WARN] {msg}")

data_cache = {
    "guilds": {}
}

def load_data():
    return data_cache

async def save_data():
    try:
        with open(DATA_FILE, "wb") as f:
            f.write(orjson.dumps(data_cache))
    except Exception as e:
        warn(f"save failed: {e}")

def get_prefix(bot, message):
    if not message.guild:
        return commands.when_mentioned_or(DEFAULT_PREFIX)(bot, message)

    prefix = data_cache.get("guilds", {}).get(str(message.guild.id), {}).get("prefix", DEFAULT_PREFIX)

    return commands.when_mentioned_or(prefix)(bot, message)

bot = commands.Bot(
    command_prefix=get_prefix,
    intents=discord.Intents.all(),
    help_command=None
)

bot.load_data = load_data
bot.save_data = save_data

async def sendmessage(ctx, *args, **kwargs):
    try:
        interaction = getattr(ctx, "interaction", None)

        if interaction:
            if not interaction.response.is_done():
                return await interaction.response.send_message(*args, **kwargs)
            return await interaction.followup.send(*args, **kwargs)

        if hasattr(ctx, "reply"):
            return await ctx.reply(*args, mention_author=False, **kwargs)

        return await ctx.send(*args, **kwargs)

    except Exception as e:
        warn(f"send failed: {e}")

bot.sendmessage = sendmessage

def scan_extensions():
    extensions = []

    for base in ("commands", "utility"):
        path = Path(base)

        if not path.exists():
            continue

        for file in path.rglob("*.py"):
            if file.name == "__init__.py":
                continue

            if any(part.lower() in IGNORED_FOLDERS for part in file.parts):
                continue

            module = str(file).replace("\\", ".").replace("/", ".").removesuffix(".py")

            if ".events." in module:
                continue

            extensions.append(module)

    return extensions

async def load_extensions():
    for ext in scan_extensions():
        try:
            await bot.load_extension(ext)
            print(f"[LOADED] {ext}")
        except Exception as e:
            warn(f"load fail {ext}: {e}")

async def reload_extensions():
    for ext in scan_extensions():
        try:
            if ext in bot.extensions:
                await bot.reload_extension(ext)
            else:
                await bot.load_extension(ext)

            print(f"[RELOADED] {ext}")
        except Exception as e:
            warn(f"reload fail {ext}: {e}")

@bot.event
async def setup_hook():
    bot.start_time = time.time()
    await load_extensions()

    try:
        await bot.tree.sync()
    except Exception as e:
        warn(f"sync failed: {e}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_command_error(ctx, error):
    if hasattr(ctx.command, "on_error"):
        return

    while hasattr(error, "original"):
        error = error.original

    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.MissingPermissions):
        perms = ", ".join(error.missing_permissions)
        return await bot.sendmessage(ctx, f"missing permissions: `{perms}`")

    if isinstance(error, commands.BotMissingPermissions):
        perms = ", ".join(error.missing_permissions)
        return await bot.sendmessage(ctx, f"bot missing permissions: `{perms}`")

    if isinstance(error, commands.CommandOnCooldown):
        return await bot.sendmessage(ctx, f"cooldown: {round(error.retry_after, 1)}s")

    if isinstance(error, commands.MissingRequiredArgument):
        return await bot.sendmessage(ctx, f"missing argument: `{error.param.name}`")

    if isinstance(error, commands.MissingRequiredAttachment):
        return await bot.sendmessage(ctx, f"missing attachment: `{error.param.name}`")

    if isinstance(error, commands.BadUnionArgument):
        return await bot.sendmessage(ctx, f"invalid value for `{error.param.name}`")

    if isinstance(error, commands.BadLiteralArgument):
        return await bot.sendmessage(ctx, f"invalid choice for `{error.param.name}`")

    if isinstance(error, commands.BadArgument):
        return await bot.sendmessage(ctx, "invalid argument")

    if isinstance(error, commands.TooManyArguments):
        return await bot.sendmessage(ctx, "too many arguments")

    if isinstance(error, commands.NotOwner):
        return await bot.sendmessage(ctx, "owner only")

    if isinstance(error, commands.NoPrivateMessage):
        return await bot.sendmessage(ctx, "guild only")

    if isinstance(error, commands.CheckFailure):
        return await bot.sendmessage(ctx, "permission denied")

    if isinstance(error, discord.Forbidden):
        return await bot.sendmessage(ctx, "bot doesn't have permission to do that")

    if isinstance(error, discord.NotFound):
        return await bot.sendmessage(ctx, "target not found")

    if isinstance(error, discord.HTTPException):
        return await bot.sendmessage(ctx, "discord api error")

    warn(f"unhandled error: {error}")
    await bot.sendmessage(ctx, "unexpected error")

def get_category(command):
    module = command.cog.__module__ if command.cog else ""
    parts = module.split(".")
    return parts[1].capitalize() if len(parts) >= 2 else "Other"

class HelpView(discord.ui.View):
    def __init__(self, ctx, category_map):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.category_map = category_map
        self.category = None
        self.page = 0
        self.state = "menu"
        self.update_items()

    async def interaction_check(self, interaction):
        return interaction.user.id == self.ctx.author.id

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

    def pages(self):
        cmds = self.category_map[self.category]
        return [cmds[i:i + 10] for i in range(0, len(cmds), 10)]

    def embed(self):
        gid = str(self.ctx.guild.id) if self.ctx.guild else None

        prefix = data_cache.get("guilds", {}).get(gid, {}).get("prefix", DEFAULT_PREFIX)

        pages = self.pages()

        embed = discord.Embed(
            title=self.category,
            description=f"Prefix: `{prefix}`",
            color=discord.Color.blurple()
        )

        for cmd in pages[self.page]:
            embed.add_field(
                name=cmd["name"],
                value=cmd["description"],
                inline=False
            )

        embed.set_footer(text=f"Page {self.page + 1}/{len(pages)}")
        return embed

    def update_items(self):
        self.clear_items()

        if self.state == "menu":
            self.add_item(CategorySelect(self))
            return

        pages = self.pages()

        self.add_item(self.PrevButton(
            disabled=len(pages) <= 1 or self.page <= 0
        ))

        self.add_item(self.NextButton(
            disabled=len(pages) <= 1 or self.page >= len(pages) - 1
        ))

        self.add_item(self.BackButton())

    class PrevButton(discord.ui.Button):
        def __init__(self, disabled=False):
            super().__init__(label="<", style=discord.ButtonStyle.blurple, disabled=disabled)

        async def callback(self, interaction):
            view = self.view
            view.page -= 1
            view.update_items()
            await interaction.response.edit_message(embed=view.embed(), view=view)

    class NextButton(discord.ui.Button):
        def __init__(self, disabled=False):
            super().__init__(label=">", style=discord.ButtonStyle.blurple, disabled=disabled)

        async def callback(self, interaction):
            view = self.view
            view.page += 1
            view.update_items()
            await interaction.response.edit_message(embed=view.embed(), view=view)

    class BackButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Back", style=discord.ButtonStyle.red)

        async def callback(self, interaction):
            view = self.view
            view.state = "menu"
            view.category = None
            view.page = 0
            view.update_items()
            await interaction.response.edit_message(embed=None, view=view)

class CategorySelect(discord.ui.Select):
    def __init__(self, view):
        self.view_ref = view

        super().__init__(
            placeholder="Select category...",
            options=[
                discord.SelectOption(label=category, value=category)
                for category in view.category_map
            ]
        )

    async def callback(self, interaction):
        view = self.view_ref
        view.state = "category"
        view.category = self.values[0]
        view.page = 0
        view.update_items()
        await interaction.response.edit_message(embed=view.embed(), view=view)

@bot.hybrid_command(description="Display help menu")
async def help(ctx):
    category_map = {}
    seen = set()

    def add(category, name, description):
        key = name.lower()
        if key in seen:
            return
        seen.add(key)
        category_map.setdefault(category, []).append({
            "name": name,
            "description": description or "No description"
        })

    def walk_prefix(cmd, parent=None):
        if cmd.hidden:
            return

        name = f"{parent} {cmd.name}" if parent else cmd.name
        category = get_category(cmd)

        if category != "Other":
            add(category, name, cmd.description)

        if isinstance(cmd, commands.Group):
            for sub in cmd.commands:
                walk_prefix(sub, name)

    for cmd in bot.commands:
        walk_prefix(cmd)

    for cmd in bot.tree.get_commands():
        module = cmd.callback.__module__ if hasattr(cmd, "callback") else ""
        parts = module.split(".")
        category = parts[1].capitalize() if len(parts) >= 2 else "Other"

        if category == "Other":
            continue

        add(category, cmd.name, getattr(cmd, "description", None))

    if not category_map:
        return await ctx.send("no commands")

    await bot.sendmessage(ctx, view=HelpView(ctx, category_map))

@bot.hybrid_command()
@commands.is_owner()
async def reload(ctx):
    await reload_extensions()
    await ctx.send("reloaded")

@bot.hybrid_command()
@commands.is_owner()
async def restart(ctx):
    await ctx.send("restarting...")
    await bot.close()
    os._exit(0)

@bot.hybrid_command()
@commands.has_permissions(administrator=True)
async def setprefix(ctx, prefix: str):
    if not ctx.guild:
        return

    gid = str(ctx.guild.id)

    data_cache.setdefault("guilds", {})
    data_cache["guilds"].setdefault(gid, {})
    data_cache["guilds"][gid]["prefix"] = prefix

    await save_data()
    await ctx.send(f"prefix set to `{prefix}`")

try:
    if os.path.isfile(DATA_FILE):
        with open(DATA_FILE, "rb") as f:
            loaded = orjson.loads(f.read())

        if isinstance(loaded, dict):
            data_cache.clear()
            data_cache.update(loaded)
except Exception as e:
    warn(f"load failed: {e}")

bot.run(TOKEN)