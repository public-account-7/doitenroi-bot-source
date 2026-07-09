from discord.ext import commands
import discord
from discord import app_commands
import json
import base64
import hashlib
import io
import secrets
import asyncio
import time

SECRET_KEY = "HUiuejrPbUudXS3PhD6VyvucELQmF2jj"

class RestoreTimeout(Exception):
    pass

def _keystream(length: int):
    key = hashlib.sha256(SECRET_KEY.encode()).digest()
    out = b""
    counter = 0
    while len(out) < length:
        counter_bytes = counter.to_bytes(4, "big")
        out += hashlib.sha256(key + counter_bytes).digest()
        counter += 1
    return out[:length]

def encrypt(data: str):
    raw = data.encode()
    ks = _keystream(len(raw))
    return base64.b64encode(bytes(a ^ b for a, b in zip(raw, ks))).decode()

def decrypt(data: str):
    raw = base64.b64decode(data.encode())
    ks = _keystream(len(raw))
    return bytes(a ^ b for a, b in zip(raw, ks)).decode()

def owner_or_admin():
    async def predicate(ctx):
        if await ctx.bot.is_owner(ctx.author):
            return True
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)

class ServerBackup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _start_timer(self):
        return time.monotonic()

    def _check_timeout(self, start, limit=300):
        if time.monotonic() - start > limit:
            raise RestoreTimeout()

    async def safe_call(self, coro, start):
        while True:
            self._check_timeout(start)
            try:
                return await coro
            except discord.Forbidden:
                return None
            except discord.HTTPException as e:
                self._check_timeout(start)
                if e.status == 429:
                    retry_after = getattr(e, "retry_after", 2)
                    await asyncio.sleep(float(retry_after))
                else:
                    await asyncio.sleep(1)

    @commands.hybrid_command(name="backupserver", description="backup server to a file")
    @owner_or_admin()
    @commands.guild_only()
    async def backupserver(self, ctx):
        guild = ctx.guild

        backup = {
            "name": guild.name,
            "roles": [],
            "categories": [],
            "channels": []
        }

        for role in guild.roles:
            if role.managed:
                continue
            backup["roles"].append({
                "name": role.name,
                "color": role.color.value,
                "permissions": role.permissions.value,
                "position": role.position,
                "hoist": role.hoist,
                "mentionable": role.mentionable,
                "default": role.is_default(),
                "managed": role.managed
            })

        for cat in guild.categories:
            backup["categories"].append({
                "name": cat.name,
                "position": cat.position
            })

        for ch in guild.channels:
            data = {
                "name": ch.name,
                "type": str(ch.type),
                "position": ch.position,
                "category": ch.category.name if ch.category else None,
                "overwrites": []
            }

            for target, overwrite in ch.overwrites.items():
                data["overwrites"].append({
                    "name": getattr(target, "name", None),
                    "id": target.id,
                    "type": "role" if isinstance(target, discord.Role) else "member",
                    "allow": overwrite.pair()[0].value,
                    "deny": overwrite.pair()[1].value
                })

            if isinstance(ch, discord.TextChannel):
                data["topic"] = ch.topic
                data["slowmode"] = ch.slowmode_delay

            if isinstance(ch, discord.VoiceChannel):
                data["bitrate"] = ch.bitrate
                data["user_limit"] = ch.user_limit

            backup["channels"].append(data)

        raw = json.dumps(backup)
        encrypted = encrypt(raw)

        filename = f"{secrets.token_hex(8)}.txt"
        file = discord.File(io.BytesIO(encrypted.encode()), filename=filename)

        try:
            await ctx.author.send("uh to use ts file just add bot to server u wanna restore then use command `/restorebackup` with that file and just waiting", file=file)
            await self.bot.sendmessage(ctx, "backup sent to dm.")
        except:
            await self.bot.sendmessage(ctx, "failed to dm you.")

    @app_commands.command(name="restorebackup", description="restore server from backup file")
    async def restorebackup(self, interaction: discord.Interaction, data: discord.Attachment):
        await interaction.response.defer(thinking=True)

        guild = interaction.guild
        me = guild.me
        start = self._start_timer()

        if interaction.user.id != guild.owner_id:
            return await interaction.followup.send("only server owner can use this.")

        if not me.guild_permissions.administrator:
            return await interaction.followup.send("bot need admin permission.")

        try:
            await interaction.user.send("processing...")
        except:
            pass

        try:
            content = await data.read()
            decrypted = decrypt(content.decode())
            data = json.loads(decrypted)
        except:
            return await interaction.followup.send("invalid backup.")

        try:
            for ch in list(guild.channels):
                self._check_timeout(start)
                if ch.permissions_for(me).manage_channels:
                    await self.safe_call(ch.delete(), start)

            for role in list(guild.roles):
                self._check_timeout(start)
                if role.is_default() or role.managed:
                    continue
                if role < me.top_role:
                    await self.safe_call(role.delete(), start)

            role_map = {}
            sorted_roles = sorted(data["roles"], key=lambda x: x["position"], reverse=True)

            for r in sorted_roles:
                self._check_timeout(start)

                if r.get("managed"):
                    continue

                if r.get("default"):
                    role_map[r["name"]] = guild.default_role
                    continue

                role = await self.safe_call(guild.create_role(
                    name=r["name"],
                    permissions=discord.Permissions(r["permissions"]),
                    colour=discord.Colour(r["color"]),
                    hoist=r["hoist"],
                    mentionable=r["mentionable"]
                ), start)

                if role:
                    role_map[r["name"]] = role

            try:
                position_map = {}
                for r in data["roles"]:
                    self._check_timeout(start)
                    if r.get("managed") or r.get("default"):
                        continue
                    role = role_map.get(r["name"])
                    if role:
                        position_map[role] = r["position"]
                await guild.edit_role_positions(position_map)
            except:
                pass

            cat_map = {}
            for c in sorted(data["categories"], key=lambda x: x["position"]):
                self._check_timeout(start)
                cat = await self.safe_call(guild.create_category(c["name"]), start)
                if cat:
                    cat_map[c["name"]] = cat

            for ch in sorted(data["channels"], key=lambda x: x["position"]):
                self._check_timeout(start)

                overwrites = {}
                for ow in ch["overwrites"]:
                    target = None
                    if ow["type"] == "role":
                        target = role_map.get(ow["name"])
                    elif ow["type"] == "member":
                        target = guild.get_member(ow["id"])

                    if target:
                        overwrites[target] = discord.PermissionOverwrite.from_pair(
                            discord.Permissions(ow["allow"]),
                            discord.Permissions(ow["deny"])
                        )

                category = cat_map.get(ch["category"])

                if "text" in ch["type"]:
                    await self.safe_call(guild.create_text_channel(
                        ch["name"],
                        category=category,
                        topic=ch.get("topic"),
                        slowmode_delay=ch.get("slowmode", 0),
                        overwrites=overwrites
                    ), start)

                elif "voice" in ch["type"]:
                    await self.safe_call(guild.create_voice_channel(
                        ch["name"],
                        category=category,
                        bitrate=ch.get("bitrate", 64000),
                        user_limit=ch.get("user_limit", 0),
                        overwrites=overwrites
                    ), start)

            await interaction.user.send("server restored successfully.")

        except RestoreTimeout:
            try:
                await interaction.user.send("restore failed: timeout (5 minutes exceeded).")
            except:
                pass

async def setup(bot):
    await bot.add_cog(ServerBackup(bot))
