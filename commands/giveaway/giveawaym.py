from discord.ext import commands
import discord
import asyncio
import random

from datetime import (
    datetime,
    timedelta,
    timezone
)


class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def update_embed(
        self,
        interaction,
        entry
    ):
        try:
            embed = (
                interaction.message.embeds[0]
                if interaction.message.embeds
                else discord.Embed()
            )

            count = len(entry["entries"])

            desc = embed.description or ""

            lines = [
                l
                for l in desc.split("\n")
                if not l.startswith(
                    "Participants:"
                )
            ]

            lines.append(
                f"Participants: {count}"
            )

            embed.description = "\n".join(
                lines
            )

            await interaction.message.edit(
                embed=embed,
                view=self
            )

        except Exception as e:
            print(
                f"[WARN] update embed error: {e}"
            )

    @discord.ui.button(
        label="Join Giveaway",
        style=discord.ButtonStyle.green,
        custom_id="giveaway_join"
    )
    async def join(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        try:
            if not interaction.guild:
                return await interaction.response.send_message(
                    "guild only",
                    ephemeral=True
                )

            guilds = (
                interaction.client
                .load_data()
                .setdefault(
                    "guilds",
                    {}
                )
            )

            g = guilds.setdefault(
                str(interaction.guild.id),
                {}
            )

            gw = g.setdefault(
                "giveaways",
                {}
            )

            msg_id = str(
                interaction.message.id
            )

            entry = gw.get(msg_id)

            if not entry:
                return await interaction.response.send_message(
                    "giveaway not found",
                    ephemeral=True
                )

            if interaction.user.id in entry["entries"]:
                entry["entries"].remove(
                    interaction.user.id
                )

                await interaction.client.save_data()

                await self.update_embed(
                    interaction,
                    entry
                )

                return await interaction.response.send_message(
                    "left giveaway",
                    ephemeral=True
                )

            entry["entries"].append(
                interaction.user.id
            )

            await interaction.client.save_data()

            await self.update_embed(
                interaction,
                entry
            )

            await interaction.response.send_message(
                "joined giveaway",
                ephemeral=True
            )

        except Exception as e:
            print(
                f"[WARN] giveaway join error: {e}"
            )


class Giveawaym(commands.Cog):
    CLEANUP_DAYS = 14

    def __init__(
        self,
        bot
    ):
        self.bot = bot

        bot.add_view(
            GiveawayView()
        )

        self.restore_task = asyncio.create_task(
            self.restore_giveaways()
        )

        self.cleanup_task = asyncio.create_task(
            self.cleanup_old_giveaways()
        )

    giveaway = discord.app_commands.Group(
        name="giveaway",
        description="giveaway commands"
    )

    def parse_time(
        self,
        t
    ):
        try:
            unit = t[-1]

            val = int(t[:-1])

            if unit == "s":
                return timedelta(
                    seconds=val
                )

            if unit == "m":
                return timedelta(
                    minutes=val
                )

            if unit == "h":
                return timedelta(
                    hours=val
                )

            if unit == "d":
                return timedelta(
                    days=val
                )

            if unit == "w":
                return timedelta(
                    weeks=val
                )

            if unit == "M":
                return timedelta(
                    days=val * 30
                )

            if unit == "y":
                return timedelta(
                    days=val * 365
                )

        except:
            return None

    async def restore_giveaways(self):
        await self.bot.wait_until_ready()

        try:
            guilds = (
                self.bot
                .load_data()
                .get(
                    "guilds",
                    {}
                )
            )

            for gid, gdata in guilds.items():
                for msg_id, entry in (
                    gdata
                    .get(
                        "giveaways",
                        {}
                    )
                    .items()
                ):
                    if entry.get(
                        "ended"
                    ):
                        continue

                    end = entry["end"]

                    now = int(
                        datetime.now(
                            timezone.utc
                        ).timestamp()
                    )

                    remaining = end - now

                    if remaining <= 0:
                        asyncio.create_task(
                            self.finish_giveaway(
                                int(gid),
                                int(msg_id)
                            )
                        )

                    else:
                        asyncio.create_task(
                            self.wait_and_finish(
                                int(gid),
                                int(msg_id),
                                remaining
                            )
                        )

        except Exception as e:
            print(
                f"[WARN] restore giveaways error: {e}"
            )

    async def wait_and_finish(
        self,
        gid,
        msg_id,
        delay
    ):
        await asyncio.sleep(
            int(delay)
        )

        await self.finish_giveaway(
            gid,
            msg_id
        )

    async def finish_giveaway(
        self,
        gid,
        msg_id
    ):
        try:
            guilds = (
                self.bot
                .load_data()
                .get(
                    "guilds",
                    {}
                )
            )

            g = guilds.get(
                str(gid),
                {}
            )

            gw = g.get(
                "giveaways",
                {}
            )

            entry = gw.get(
                str(msg_id)
            )

            if (
                not entry
                or
                entry.get("ended")
            ):
                return

            guild = self.bot.get_guild(
                gid
            )

            if not guild:
                return

            channel = guild.get_channel(
                entry["channel"]
            )

            if not channel:
                return

            try:
                message = await channel.fetch_message(
                    msg_id
                )

            except:
                message = None

            users = entry.get(
                "entries",
                []
            )

            winner_count = max(
                0,
                min(
                    len(users),
                    entry["winners"]
                )
            )

            winners = (
                random.sample(
                    users,
                    winner_count
                )
                if winner_count > 0
                else []
            )

            entry["last_winners"] = winners

            entry["ended"] = True

            entry["ended_at"] = int(
                datetime.now(
                    timezone.utc
                ).timestamp()
            )

            await self.bot.save_data()

            if message:
                embed = (
                    message.embeds[0]
                    if message.embeds
                    else discord.Embed()
                )

                embed.color = discord.Color.red()

                embed.title = "Giveaway Ended"

                desc_lines = []

                desc_lines.append(
                    f"Prize: **{entry['prize']}**"
                )

                desc_lines.append(
                    f"Winners: **{entry['winners']}**"
                )

                desc_lines.append(
                    f"Participants: {len(users)}"
                )

                if entry.get("host"):
                    desc_lines.append(
                        f"Hosted by: <@{entry['host']}>"
                    )

                if winners:
                    mentions = " ".join(
                        f"<@{u}>"
                        for u in winners
                    )

                    desc_lines.append(
                        f"Winners: {mentions}"
                    )

                else:
                    desc_lines.append(
                        "Winners: No participants"
                    )

                embed.description = "\n".join(
                    desc_lines
                )

                try:
                    await message.edit(
                        embed=embed,
                        view=None
                    )

                except Exception as e:
                    print(
                        f"[WARN] edit embed failed: {e}"
                    )

            if winners:
                mentions = " ".join(
                    f"<@{u}>"
                    for u in winners
                )

                if message:
                    await message.reply(
                        f"Winners: {mentions} | Prize: **{entry['prize']}**",
                        mention_author=False
                    )

                else:
                    await channel.send(
                        f"Winners: {mentions} | Prize: **{entry['prize']}**"
                    )

            else:
                if message:
                    await message.reply(
                        "no participants",
                        mention_author=False
                    )

                else:
                    await channel.send(
                        "no participants"
                    )

        except Exception as e:
            print(
                f"[WARN] finish giveaway error: {e}"
            )

    async def cleanup_old_giveaways(self):
        await self.bot.wait_until_ready()

        while True:
            try:
                guilds = (
                    self.bot
                    .load_data()
                    .get(
                        "guilds",
                        {}
                    )
                )

                now_ts = int(
                    datetime.now(
                        timezone.utc
                    ).timestamp()
                )

                changed = False

                for gid, gdata in guilds.items():
                    gw = gdata.get(
                        "giveaways",
                        {}
                    )

                    to_remove = []

                    for msg_id, entry in gw.items():
                        if (
                            entry.get("ended")
                            and
                            entry.get("ended_at")
                        ):
                            if (
                                now_ts
                                -
                                entry["ended_at"]
                            ) > (
                                self.CLEANUP_DAYS
                                *
                                86400
                            ):
                                to_remove.append(
                                    msg_id
                                )

                    for msg_id in to_remove:
                        gw.pop(
                            msg_id,
                            None
                        )

                        changed = True

                if changed:
                    await self.bot.save_data()

            except Exception as e:
                print(
                    f"[WARN] cleanup error: {e}"
                )

            await asyncio.sleep(3600)

    @giveaway.command(
        name="create",
        description="start a giveaway"
    )
    @discord.app_commands.checks.has_permissions(
        manage_guild=True
    )
    async def create(
        self,
        interaction: discord.Interaction,
        prize: str,
        winners: int,
        duration: str,
        channel: discord.TextChannel = None,
        host: discord.Member = None
    ):
        try:
            if not interaction.guild:
                return await interaction.response.send_message(
                    "guild only",
                    ephemeral=True
                )

            delta = self.parse_time(
                duration
            )

            if not delta:
                return await interaction.response.send_message(
                    "invalid duration",
                    ephemeral=True
                )

            end_time = (
                datetime.now(
                    timezone.utc
                )
                +
                delta
            )

            ch = (
                channel
                or
                interaction.channel
            )

            desc_lines = []

            desc_lines.append(
                f"Prize: **{prize}**"
            )

            desc_lines.append(
                f"Winners: **{winners}**"
            )

            desc_lines.append(
                f"Ends: <t:{int(end_time.timestamp())}:R>"
            )

            desc_lines.append(
                "Participants: 0"
            )

            if host:
                desc_lines.append(
                    f"Hosted by: {host.mention}"
                )

            embed = discord.Embed(
                title="Giveaway",
                description="\n".join(
                    desc_lines
                ),
                color=discord.Color.blurple()
            )

            view = GiveawayView()

            msg = await ch.send(
                embed=embed,
                view=view
            )

            await interaction.response.send_message(
                "giveaway started",
                ephemeral=True
            )

            guilds = (
                self.bot
                .load_data()
                .setdefault(
                    "guilds",
                    {}
                )
            )

            g = guilds.setdefault(
                str(interaction.guild.id),
                {}
            )

            gw = g.setdefault(
                "giveaways",
                {}
            )

            gw[str(msg.id)] = {
                "prize": prize,
                "winners": winners,
                "end": int(
                    end_time.timestamp()
                ),
                "entries": [],
                "channel": ch.id,
                "last_winners": [],
                "host": (
                    host.id
                    if host
                    else None
                ),
                "ended": False,
                "ended_at": None
            }

            await self.bot.save_data()

            asyncio.create_task(
                self.wait_and_finish(
                    interaction.guild.id,
                    msg.id,
                    int(
                        delta.total_seconds()
                    )
                )
            )

        except Exception as e:
            print(
                f"[WARN] giveaway command error: {e}"
            )

    @giveaway.command(
        name="reroll",
        description="reroll a giveaway"
    )
    @discord.app_commands.checks.has_permissions(
        manage_guild=True
    )
    async def reroll(
        self,
        interaction: discord.Interaction,
        message_id: str,
        winners: int = None,
        skip_old_winners: bool = False
    ):
        try:
            if not interaction.guild:
                return await interaction.response.send_message(
                    "guild only",
                    ephemeral=True
                )

            guilds = (
                self.bot
                .load_data()
                .get(
                    "guilds",
                    {}
                )
            )

            g = guilds.get(
                str(interaction.guild.id),
                {}
            )

            gw = g.get(
                "giveaways",
                {}
            )

            entry = gw.get(
                str(message_id)
            )

            if not entry:
                return await interaction.response.send_message(
                    "giveaway not found",
                    ephemeral=True
                )

            users = entry[
                "entries"
            ][:]

            if skip_old_winners:
                users = [
                    u
                    for u in users
                    if u not in entry.get(
                        "last_winners",
                        []
                    )
                ]

            if not users:
                return await interaction.response.send_message(
                    "no valid participants",
                    ephemeral=True
                )

            count = winners or entry.get(
                "winners",
                1
            )

            count = max(
                0,
                min(
                    len(users),
                    count
                )
            )

            new_winners = random.sample(
                users,
                count
            )

            entry["last_winners"] = (
                new_winners
            )

            await self.bot.save_data()

            mentions = " ".join(
                f"<@{u}>"
                for u in new_winners
            )

            await interaction.response.send_message(
                f"Rerolled Winners: {mentions}"
            )

        except Exception as e:
            print(
                f"[WARN] reroll error: {e}"
            )

    @giveaway.command(
        name="end",
        description="end a giveaway"
    )
    @discord.app_commands.checks.has_permissions(
        manage_guild=True
    )
    async def end(
        self,
        interaction: discord.Interaction,
        message_id: str
    ):
        try:
            if not interaction.guild:
                return await interaction.response.send_message(
                    "guild only",
                    ephemeral=True
                )

            await self.finish_giveaway(
                interaction.guild.id,
                int(message_id)
            )

            await interaction.response.send_message(
                "giveaway ended"
            )

        except Exception as e:
            print(
                f"[WARN] giveaway end error: {e}"
            )

    @giveaway.command(
        name="cancel",
        description="cancel a giveaway"
    )
    @discord.app_commands.checks.has_permissions(
        manage_guild=True
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        message_id: str
    ):
        try:
            if not interaction.guild:
                return await interaction.response.send_message(
                    "guild only",
                    ephemeral=True
                )

            guilds = (
                self.bot
                .load_data()
                .get(
                    "guilds",
                    {}
                )
            )

            g = guilds.get(
                str(interaction.guild.id),
                {}
            )

            gw = g.get(
                "giveaways",
                {}
            )

            entry = gw.get(
                str(message_id)
            )

            if not entry:
                return await interaction.response.send_message(
                    "giveaway not found",
                    ephemeral=True
                )

            guild = interaction.guild

            channel = guild.get_channel(
                entry["channel"]
            )

            try:
                message = await channel.fetch_message(
                    int(message_id)
                )

                embed = (
                    message.embeds[0]
                    if message.embeds
                    else discord.Embed()
                )

                embed.color = (
                    discord.Color.dark_gray()
                )

                embed.title = (
                    "Giveaway Cancelled"
                )

                await message.edit(
                    embed=embed,
                    view=None
                )

            except Exception as e:
                print(
                    f"[WARN] cancel edit error: {e}"
                )

            gw.pop(
                str(message_id),
                None
            )

            await self.bot.save_data()

            await interaction.response.send_message(
                "giveaway cancelled"
            )

        except Exception as e:
            print(
                f"[WARN] giveaway cancel error: {e}"
            )


async def setup(bot):
    await bot.add_cog(
        Giveawaym(bot)
    )