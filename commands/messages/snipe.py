import discord

from discord.ext import commands


class SnipeView(discord.ui.View):
    def __init__(
        self,
        ctx,
        snipes
    ):
        super().__init__(timeout=60)

        self.ctx = ctx
        self.snipes = snipes
        self.index = len(snipes) - 1

    def limit(
        self,
        text,
        max_length=1000
    ):
        if not text:
            return "*none*"

        text = str(text)

        if len(text) > max_length:
            return (
                text[:max_length - 3]
                +
                "..."
            )

        return text

    def build_embed(self):
        data = self.snipes[self.index]

        embed = discord.Embed(
            color=discord.Color.blurple()
        )

        status = (
            "edited"
            if data.get("edited")
            else "deleted"
        )

        embed.set_author(
            name=f"{data.get('author')} ({status})",
            icon_url=data.get("avatar")
        )

        if data.get("edited"):
            embed.add_field(
                name="Before",
                value=self.limit(
                    data.get("content")
                ),
                inline=False
            )

            embed.add_field(
                name="After",
                value=self.limit(
                    data.get("after")
                ),
                inline=False
            )

        else:
            embed.add_field(
                name="Message",
                value=self.limit(
                    data.get("content")
                ),
                inline=False
            )

        if data.get("channel"):
            embed.add_field(
                name="Channel",
                value=f"<#{data.get('channel')}>",
                inline=True
            )
            
        if data.get("reply_url"):
            embed.add_field(
                name="Replied Message",
                value=f"[Jump]({data.get('reply_url')})",
                inline=True
            )

        timestamp = data.get("timestamp")

        if timestamp:
            try:
                embed.timestamp = discord.utils.parse_time(
                    timestamp
                )

            except:
                pass

        embed.set_footer(
            text=f"{self.index + 1}/{len(self.snipes)}"
        )

        return embed

    def resolve_files(self):
        data = self.snipes[self.index]

        files = []

        if data.get("edited"):
            files.extend(
                data.get(
                    "files_before",
                    []
                )
            )

            files.extend(
                data.get(
                    "files_after",
                    []
                )
            )

        else:
            files.extend(
                data.get(
                    "files",
                    []
                )
            )

        formatted = []

        for file in files:
            if "|URL:" not in file:
                continue

            name, url = file.split(
                "|URL:",
                1
            )

            if not url:
                continue

            formatted.append(
                f"[{name}]({url})"
            )

        return formatted

    async def build(self):
        embed = self.build_embed()

        files = self.resolve_files()

        if files:
            files_text = "\n".join(
                files[:15]
            )

            embed.add_field(
                name="Files",
                value=self.limit(
                    files_text
                ),
                inline=False
            )

        return embed, []

    @discord.ui.button(
        label="<",
        style=discord.ButtonStyle.gray
    )
    async def prev(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message(
                "not yours",
                ephemeral=True
            )

        if self.index > 0:
            self.index -= 1

        embed, files = await self.build()

        await interaction.response.edit_message(
            embed=embed,
            attachments=files,
            view=self
        )

    @discord.ui.button(
        label=">",
        style=discord.ButtonStyle.gray
    )
    async def next(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message(
                "not yours",
                ephemeral=True
            )

        if self.index < len(self.snipes) - 1:
            self.index += 1

        embed, files = await self.build()

        await interaction.response.edit_message(
            embed=embed,
            attachments=files,
            view=self
        )


class Snipe(commands.Cog):
    def __init__(
        self,
        bot
    ):
        self.bot = bot

    @commands.hybrid_command(
        name="snipe",
        description="view deleted or edited messages"
    )
    async def snipe(
        self,
        ctx
    ):
        if not ctx.guild:
            return await ctx.send(
                "server only"
            )

        guild_data = (
            self.bot.load_data()
            .get("guilds", {})
            .get(
                str(ctx.guild.id),
                {}
            )
        )

        snipes = guild_data.get(
            "snipes",
            []
        )

        if not snipes:
            return await ctx.send(
                "nothing to snipe"
            )

        view = SnipeView(
            ctx,
            snipes
        )

        embed, files = await view.build()

        await ctx.send(
            embed=embed,
            files=files,
            view=view
        )


async def setup(bot):
    await bot.add_cog(
        Snipe(bot)
    )