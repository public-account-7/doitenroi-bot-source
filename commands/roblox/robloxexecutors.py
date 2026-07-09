import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone

import aiohttp

WEAO_API = "https://whatexpsare.online/api/status/exploits"
USER_AGENT = "WEAO-3PService"

from datetime import datetime, timezone

def format_last_updated(updated_date: str) -> str:
    try:
        date_part = updated_date.split(" at ")[0]
        day, month, year = map(int, date_part.split("/"))

        if day > 12:
            fmt = "%d/%m/%Y at %I:%M %p UTC"
        else:
            fmt = "%m/%d/%Y at %I:%M %p UTC"

        dt = datetime.strptime(updated_date, fmt).replace(tzinfo=timezone.utc)
        ts = int(dt.timestamp())

        if ts > datetime.now(timezone.utc).timestamp():
            return updated_date

        return f"<t:{ts}:R>"

    except:
        return updated_date

class TypeSelect(discord.ui.View):
    def __init__(self, author: discord.User, data: list, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.author = author
        self.data = data

        options = [
            discord.SelectOption(label="Android Executor", description="All Current Android Executor", value="aexecutor"),
            discord.SelectOption(label="iOS Executor", description="All Current IOS Executor", value="iexecutor"),
            discord.SelectOption(label="Windows Executor", description="All Current Windows Executor", value="wexecutor"),
            discord.SelectOption(label="Windows External", description="All Current Windows External", value="wexternal"),
            discord.SelectOption(label="Mac Executor", description="All Current Mac Executor", value="mexecutor"),
        ]

        self.select = discord.ui.Select(
            placeholder="Choose type to display...",
            min_values=1,
            max_values=1,
            options=options
        )

        self.select.callback = self._on_select
        self.add_item(self.select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("no", ephemeral=True)
            return False
        return True

    async def _on_select(self, interaction: discord.Interaction):
        self.select.disabled = True
        await interaction.response.edit_message(view=self)

        extype = self.select.values[0]
        executors = [e for e in self.data if e.get("extype") == extype]

        if not executors:
            self.select.disabled = False
            await interaction.followup.send("Not found.", ephemeral=True)
            await interaction.edit_original_response(view=self)
            return

        pager = ExploitPager(self.author, executors)
        await interaction.edit_original_response(embed=pager.get_embed(), view=pager)


class ExploitPager(discord.ui.View):
    def __init__(self, author: discord.User, exploits: list, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.author = author
        self.exploits = exploits
        self.page = 0
        self.max_page = max(len(exploits) - 1, 0)

        self.update_buttons()

    def update_buttons(self):
        try:
            self.previous_button.disabled = self.page <= 0
            self.next_button.disabled = self.page >= self.max_page
        except AttributeError:
            pass

    def bool_emoji(self, val: bool) -> str:
        return "✔" if val else "✖"

    def get_embed(self) -> discord.Embed:
        e = self.exploits[self.page]

        title = e.get("title", "Unknown")
        free = e.get("free", False)
        update_status = e.get("updateStatus", False)
        platform = e.get("platform", "Unknown")
        cost = e.get("cost") if not free else "Free"
        purchaselink = e.get("purchaselink")
        websitelink = e.get("websitelink")
        discordlink = e.get("discordlink")
        updated_date = e.get("updatedDate", "Unknown")
        sunc_pct = e.get("suncPercentage")
        unc_pct = e.get("uncPercentage")
        decompiler = e.get("decompiler", False)
        multi_inject = e.get("multiInject", False)

        embed = discord.Embed(
            title=title,
            color=discord.Color.blurple()
        )

        embed.add_field(name="Free", value=self.bool_emoji(free), inline=True)
        embed.add_field(name="Working", value=self.bool_emoji(update_status), inline=True)
        embed.add_field(name="Platform", value=platform, inline=True)

        embed.add_field(name="sUNC", value=f"{sunc_pct}%" if sunc_pct is not None else "N/A", inline=True)
        embed.add_field(name="UNC", value=f"{unc_pct}%" if unc_pct is not None else "N/A", inline=True)

        embed.add_field(name="Decompiler", value=self.bool_emoji(decompiler), inline=True)
        embed.add_field(name="Multi Inject", value=self.bool_emoji(multi_inject), inline=True)

        embed.add_field(name="Last Updated", value=format_last_updated(updated_date), inline=False)

        if not free:
            embed.add_field(name="Cost", value=cost or "Unknown", inline=False)

            if purchaselink:
                embed.add_field(name="Purchase Link", value=f"[Click Here]({purchaselink})", inline=False)

        if websitelink:
            embed.add_field(name="Website", value=f"[Click Here]({websitelink})", inline=False)

        if discordlink:
            embed.add_field(name="Discord", value=f"[Join Here]({discordlink})", inline=False)

        embed.set_footer(text=f"{self.page + 1}/{self.max_page + 1}")

        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("no", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Prev", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(0, self.page - 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = min(self.max_page, self.page + 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)


class Executors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="robloxexecutors",
        description="list all current roblox executors"
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def executors(self, ctx: commands.Context):

        await ctx.defer()

        async with aiohttp.ClientSession() as session:
            async with session.get(
                WEAO_API,
                headers={"User-Agent": USER_AGENT}
            ) as resp:

                if resp.status == 429:
                    return await self.bot.sendmessage(ctx,"rate limited, try again")

                if resp.status != 200:
                    return await self.bot.sendmessage(ctx,
                        f"Failed to fetch data. Status: {resp.status}"
                    )

                data = await resp.json()

        view = TypeSelect(ctx.author, data)

        await self.bot.sendmessage(ctx,view=view)


async def setup(bot):
    await bot.add_cog(Executors(bot))