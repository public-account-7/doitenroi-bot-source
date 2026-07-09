import discord
from discord.ext import commands
import wavelink
import asyncio
import random
import math
import urllib.parse
import time
from typing import Optional, List, Union

class QueueView(discord.ui.View):
    def __init__(self, queue: List[wavelink.Playable]):
        super().__init__(timeout=120)
        self.queue = queue
        self.current_page = 0
        self.per_page = 10
        self.max_pages = max(math.ceil(len(queue) / self.per_page), 1) if queue else 1

    def generate_embed(self) -> discord.Embed:
        embed = discord.Embed(title="Current Queue", color=discord.Color.blurple())
        if not self.queue:
            embed.description = "The queue is empty."
            return embed
        start = self.current_page * self.per_page
        end = start + self.per_page
        tracks = self.queue[start:end]
        desc = []
        for i, track in enumerate(tracks, start=start + 1):
            clean_title = track.title.replace('[', '').replace(']', '')
            safe_url = urllib.parse.quote(track.uri, safe=":/?&=")
            desc.append(f"**{i}.** [{clean_title}]({safe_url})")
        embed.description = "\n".join(desc)
        embed.set_footer(text=f"Page {self.current_page + 1} of {self.max_pages} | Total Tracks: {len(self.queue)}")
        return embed

    def update_buttons(self):
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == self.max_pages - 1

    @discord.ui.button(label="<", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @discord.ui.button(label=">", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

class Music(commands.Cog):
    LAVALINK_URI = "https://lavalinkv4.serenetia.com"
    LAVALINK_PASSWORD = "https://seretia.link/discord"

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues: dict[int, list] = {}
        self.text_channels: dict[int, discord.TextChannel] = {}
        self.leave_tasks: dict[int, asyncio.Task] = {}
        self.shuffle_states: dict[int, bool] = {}
        self.loop_states: dict[int, bool] = {}
        self.node_ready = asyncio.Event()
        self.watchdog_task: Optional[asyncio.Task] = None
        self.reconnect_lock = asyncio.Lock()

    def in_guild(self, ctx) -> bool:
        return ctx.guild is not None

    def check_voice(self, ctx) -> bool:
        return ctx.author.voice and ctx.author.voice.channel

    def same_vc(self, ctx, vc: wavelink.Player) -> bool:
        return (ctx.author.voice and vc and vc.channel and ctx.author.voice.channel.id == vc.channel.id)

    def get_queue(self, guild_id: int) -> list:
        return self.queues.setdefault(guild_id, [])

    def is_shuffle(self, guild_id: int) -> bool:
        return self.shuffle_states.get(guild_id, False)

    def toggle_shuffle(self, guild_id: int) -> bool:
        state = not self.shuffle_states.get(guild_id, False)
        self.shuffle_states[guild_id] = state
        return state

    def is_loop(self, guild_id: int) -> bool:
        return self.loop_states.get(guild_id, False)

    def toggle_loop(self, guild_id: int) -> bool:
        state = not self.loop_states.get(guild_id, False)
        self.loop_states[guild_id] = state
        return state

    def reset_guild(self, guild_id: int):
        for attr in ('queues', 'text_channels', 'shuffle_states', 'loop_states'):
            getattr(self, attr).pop(guild_id, None)

    def cancel_leave(self, guild_id: int):
        task = self.leave_tasks.pop(guild_id, None)
        if task:
            task.cancel()

    @staticmethod
    def format_time(ms: int) -> str:
        s = int(ms / 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h}:{m:02}:{s:02}"
        return f"{m}:{s:02}"

    async def ensure_node(self):
        async with self.reconnect_lock:
            if wavelink.Pool.nodes:
                node = next(iter(wavelink.Pool.nodes.values()))
                if node.status.name == "CONNECTED":
                    self.node_ready.set()
                    return True
            try:
                try:
                    await asyncio.wait_for(
                        wavelink.Pool.connect(
                            client=self.bot,
                            nodes=[
                                wavelink.Node(
                                    identifier="millohost-main",
                                    uri=self.LAVALINK_URI,
                                    password=self.LAVALINK_PASSWORD,
                                    heartbeat=15,
                                    inactive_player_timeout=0,
                                    inactive_channel_tokens=0,
                                )
                            ],
                        ),
                        timeout=20,
                    )
                except asyncio.TimeoutError:
                    print("Lavalink connection timed out")
                    self.node_ready.clear()
                    return False
                self.node_ready.set()
                return True
            except Exception as e:
                print(f"Lavalink connect failed: {e}")
                self.node_ready.clear()
                return False

    async def safe_wait_node(self):
        if wavelink.Pool.nodes:
            node = next(iter(wavelink.Pool.nodes.values()))
            if node.status.name == "CONNECTED":
                return True
        return await self.ensure_node()

    async def safe_search(self, query: str):
        if not await self.safe_wait_node():
            return []
        try:
            return await asyncio.wait_for(
                self.search_tracks(query), timeout=15
            )
        except Exception as e:
            print(f"Search error: {e}")
            return []

    async def search_tracks(self, query: str) -> Union[list, wavelink.Playlist]:
        try:
            if query.startswith(("http://", "https://")):
                return await wavelink.Playable.search(query)
            for src in ("spsearch", "scsearch"):
                try:
                    results = await wavelink.Playable.search(f"{src}:{query}")
                    if results:
                        return results
                except Exception:
                    continue
            return await wavelink.Playable.search(query)
        except Exception:
            return []

    async def node_watchdog(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                if not wavelink.Pool.nodes:
                    print("Reconnecting Lavalink...")
                    await self.ensure_node()
            except Exception as e:
                print(e)
            await asyncio.sleep(60)

    async def get_player(self, ctx):
        if not await self.safe_wait_node():
            await ctx.send("Lavalink is offline.")
            return None
        vc = ctx.voice_client
        if vc and isinstance(vc, wavelink.Player):
            return vc
        if vc:
            try:
                await vc.disconnect(force=True)
            except:
                pass
        try:
            vc = await ctx.author.voice.channel.connect(
                cls=wavelink.Player,
                self_deaf=True,
            )
            return vc
        except Exception as e:
            return None

    async def apply_natural_filter(self, player: wavelink.Player):
        try:
            await player.set_filter(
                equalizer=wavelink.Equalizer([
                    {"band": 0, "gain": -0.12},
                    {"band": 1, "gain": -0.10},
                    {"band": 2, "gain": -0.07},
                    {"band": 3, "gain": 0.03},
                    {"band": 4, "gain": 0.0},
                    {"band": 5, "gain": 0.03},
                    {"band": 6, "gain": 0.04},
                    {"band": 7, "gain": 0.03},
                    {"band": 8, "gain": 0.02},
                    {"band": 9, "gain": 0.015},
                    {"band": 10, "gain": 0.0},
                    {"band": 11, "gain": 0.0},
                    {"band": 12, "gain": 0.0},
                    {"band": 13, "gain": 0.0},
                    {"band": 14, "gain": 0.0},
                ])
            )
        except Exception:
            pass

    async def schedule_leave(self, guild: discord.Guild):
        await asyncio.sleep(300)
        vc = guild.voice_client
        if not vc or not vc.channel:
            self.leave_tasks.pop(guild.id, None)
            return
        members = [m for m in vc.channel.members if not m.bot]
        if len(members) == 0:
            try:
                if vc.playing or vc.paused:
                    if guild.id in self.queues:
                        self.queues[guild.id] = []
                    await vc.stop()
                    self.reset_guild(guild.id)
                    await vc.disconnect(force=True)
            except Exception:
                pass
            self.leave_tasks.pop(guild.id, None)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload):
        print(f"Connected to {payload.node.identifier}")
        self.node_ready.set()

    @commands.Cog.listener()
    async def on_wavelink_node_disconnected(self, payload):
        print("Lavalink disconnected")
        self.node_ready.clear()

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        player = payload.player
        if not player or not player.guild.voice_client:
            return
        guild_id = player.guild.id
        queue = self.get_queue(guild_id)
        channel = self.text_channels.get(guild_id)
        loop_enabled = self.is_loop(guild_id)

        if loop_enabled and payload.track:
            if not queue:
                try:
                    await player.play(payload.track)
                    await self.apply_natural_filter(player)
                    return
                except Exception:
                    pass
            else:
                queue.append(payload.track)

        if queue:
            track = queue.pop(0)
            try:
                await player.play(track)
                await self.apply_natural_filter(player)
                if channel:
                    clean = track.title.replace('[', '').replace(']', '')
                    url = urllib.parse.quote(track.uri, safe=":/?&=")
                    await channel.send(f"now playing: [{clean}]({url})", suppress_embeds=True)
            except Exception:
                pass
        else:
            self.shuffle_states.pop(guild_id, None)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before, after):
        vc = member.guild.voice_client
        if not vc or not vc.channel:
            return
        guild_id = member.guild.id
        members = [m for m in vc.channel.members if not m.bot]
        if len(members) == 0:
            if guild_id not in self.leave_tasks:
                self.leave_tasks[guild_id] = asyncio.create_task(self.schedule_leave(member.guild))
        else:
            self.cancel_leave(guild_id)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.ensure_node()
        if not self.watchdog_task:
            self.watchdog_task = asyncio.create_task(self.node_watchdog())

    async def cog_unload(self):
        if self.watchdog_task:
            self.watchdog_task.cancel()

    @commands.hybrid_command(name="joinvc", description="join your voice channel")
    async def joinvc(self, ctx: commands.Context):
        if not self.in_guild(ctx):
            return await ctx.send("this command only works in servers")
        if not self.check_voice(ctx):
            return await ctx.send("join a voice channel first")
        vc = ctx.voice_client
        if vc and vc.channel:
            return await ctx.send("already in voice channel")
        vc = await self.get_player(ctx)
        if not vc:
            return
        await ctx.send(f"joined {vc.channel.name}")

    @commands.hybrid_command(name="leavevc", description="leave the voice channel")
    async def leavevc(self, ctx: commands.Context):
        vc = ctx.voice_client
        if not vc:
            return await ctx.send("not connected")
        if ctx.guild.id in self.queues:
            self.queues[ctx.guild.id] = []
        self.reset_guild(ctx.guild.id)
        if vc.playing:
            await vc.stop()
        await vc.disconnect()
        await ctx.send("disconnected")

    @commands.hybrid_command(name="play", description="play a song or add it to queue")
    async def play(self, ctx: commands.Context, *, query: Optional[str] = None):
        if not self.in_guild(ctx):
            return await ctx.send("this command only works in servers")
        if not self.check_voice(ctx):
            return await ctx.send("join a voice channel first")
        vc = ctx.voice_client
        if vc:
            if vc.channel != ctx.author.voice.channel:
                if len(vc.channel.members) == 1:
                    try:
                        self.reset_guild(ctx.guild.id)
                        await vc.move_to(ctx.author.voice.channel)
                    except Exception:
                        return await ctx.send("can't move to your voice channel")
                else:
                    return await ctx.send("i'm already being used in another voice channel")
        vc = await self.get_player(ctx)
        if not vc:
            return
        self.text_channels[ctx.guild.id] = ctx.channel
        self.cancel_leave(ctx.guild.id)

        if ctx.message.attachments:
            query = ctx.message.attachments[0].url
        elif query is not None:
            query = str(query)
        if not query:
            return await ctx.send("provide a song name, url, or upload a file")

        results = await self.safe_search(query)
        if not results:
            return await ctx.send("no results found")

        queue = self.get_queue(ctx.guild.id)

        if isinstance(results, wavelink.Playlist):
            tracks = list(results.tracks)
            if not tracks:
                return await ctx.send("playlist is empty")
            queue.extend(tracks)
            if self.is_shuffle(ctx.guild.id):
                random.shuffle(queue)
            await ctx.send(f"added playlist: {getattr(results, 'name', 'playlist')} ({len(tracks)} tracks)")
            if not vc.playing and not vc.paused:
                track = queue.pop(0)
                await vc.play(track)
                await self.apply_natural_filter(vc)
                clean = track.title.replace('[', '').replace(']', '')
                url = urllib.parse.quote(track.uri, safe=":/?&=")
                await ctx.send(f"now playing: [{clean}]({url})", suppress_embeds=True)
            return

        track = results[0] if isinstance(results, list) else results
        clean = track.title.replace('[', '').replace(']', '')
        url = urllib.parse.quote(track.uri, safe=":/?&=")

        if not vc.playing and not vc.paused:
            await vc.play(track)
            await self.apply_natural_filter(vc)
            await ctx.send(f"now playing: [{clean}]({url})", suppress_embeds=True)
        else:
            queue.append(track)
            if self.is_shuffle(ctx.guild.id):
                random.shuffle(queue)
            await ctx.send(f"queued: [{clean}]({url})", suppress_embeds=True)

    @commands.hybrid_command(name="skip", description="skip the current song")
    async def skip(self, ctx: commands.Context):
        vc = ctx.voice_client
        if not vc or not vc.playing:
            return await ctx.send("nothing playing")
        if not self.same_vc(ctx, vc):
            return await ctx.send("you must be in the same voice channel")
        title = vc.current.title if vc.current else "unknown"
        await vc.stop()
        await ctx.send(f"skipped current song: {title}")

    @commands.hybrid_command(name="stop", description="stop playback and clear queue")
    async def stop(self, ctx: commands.Context):
        vc = ctx.voice_client
        if not vc:
            return await ctx.send("not connected")
        if not self.same_vc(ctx, vc):
            return await ctx.send("you must be in the same voice channel")
        if ctx.guild.id in self.queues:
            self.queues[ctx.guild.id] = []
        self.reset_guild(ctx.guild.id)
        await vc.stop()
        await ctx.send("stopped")

    @commands.hybrid_command(name="queue", description="show the current queue")
    async def queue(self, ctx: commands.Context):
        queue = self.get_queue(ctx.guild.id)
        if not queue:
            return await ctx.send("queue empty")
        view = QueueView(queue)
        view.update_buttons()
        embed = view.generate_embed()
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="nowplaying", description="show the current playing song")
    async def nowplaying(self, ctx: commands.Context):
        vc = ctx.voice_client
        if not vc:
            return await ctx.send("not connected")
        if not vc.playing:
            return await ctx.send("nothing playing")
        track = vc.current
        pos = vc.position
        dur = track.length
        clean = track.title.replace('[', '').replace(']', '')
        url = urllib.parse.quote(track.uri, safe=":/?&=")
        msg = f"[{clean}]({url})\n{self.format_time(pos)}/{self.format_time(dur)}"
        await ctx.send(msg, suppress_embeds=True)

    @commands.hybrid_command(name="shuffle", description="toggle shuffle mode")
    async def shuffle(self, ctx: commands.Context):
        state = self.toggle_shuffle(ctx.guild.id)
        if state:
            queue = self.get_queue(ctx.guild.id)
            random.shuffle(queue)
        await ctx.send("shuffle enabled" if state else "shuffle disabled")

    @commands.hybrid_command(name="loop", description="toggle loop mode")
    async def loop(self, ctx: commands.Context):
        state = self.toggle_loop(ctx.guild.id)
        await ctx.send("loop enabled" if state else "loop disabled")

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))