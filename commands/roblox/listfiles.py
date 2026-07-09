import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button

import os


STORAGE_DIR = "./storage"


class FilePager(View):
    def __init__(self, user: discord.User, files, per_page=10):
        super().__init__(timeout=300)
        self.user = user
        self.files = files
        self.per_page = per_page
        self.page = 0
        self.total_pages = (len(files) - 1) // per_page + 1
        self.update_buttons()

    # enable/disable buttons depending page
    def update_buttons(self):
        self.prev_button.disabled = self.page == 0
        self.next_button.disabled = self.page >= self.total_pages - 1

    # build embed for current page
    def get_embed(self):
        start = self.page * self.per_page
        end = start + self.per_page
        page_files = self.files[start:end]

        embed = discord.Embed(
            title="Storages:",
            color=discord.Color.green()
        )

        embed.description = "\n".join(f"`{f}`" for f in page_files)
        embed.set_footer(text=f"Page {self.page + 1}/{self.total_pages}")

        return embed

    # restrict buttons to command user
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "no u cant use this button black",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Prev", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: Button):
        self.page -= 1
        self.update_buttons()
        await interaction.response.edit_message(
            embed=self.get_embed(),
            view=self
        )

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        self.page += 1
        self.update_buttons()
        await interaction.response.edit_message(
            embed=self.get_embed(),
            view=self
        )


class ListFiles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="listfiles",
        description="list all files in storage"
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def listfiles(self, ctx: commands.Context):

        os.makedirs(STORAGE_DIR, exist_ok=True)

        files = sorted(os.listdir(STORAGE_DIR))
        if not files:
            return await ctx.send("No files found in storage.")

        pager = FilePager(ctx.author, files)

        await ctx.send(
            embed=pager.get_embed(),
            view=pager
        )


async def setup(bot):
    await bot.add_cog(ListFiles(bot))