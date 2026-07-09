from discord.ext import commands
import discord

class MsgLBView(discord.ui.View):
    def __init__(self, bot, ctx, users, per):
        super().__init__(timeout=60)
        self.bot = bot
        self.ctx = ctx
        self.users = users
        self.per = per
        self.page = 1
        self.total_pages = (len(users) + per - 1) // per

    def get_embed(self):
        start = (self.page - 1) * self.per
        page_users = self.users[start:start + self.per]

        lines = [
            f"**#{i}** <@{u}> - **{c}** messages"
            for i, (u, c) in enumerate(page_users, start=start + 1)
        ]

        embed = discord.Embed(
            title="Leaderboard",
            description="\n".join(lines),
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"{self.page}/{self.total_pages}")
        return embed

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user == self.ctx.author

    @discord.ui.button(label="<", style=discord.ButtonStyle.gray)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 1:
            self.page -= 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label=">", style=discord.ButtonStyle.gray)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.total_pages:
            self.page += 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)


class MsgLB(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="msglb",
        description="show message leaderboard"
    )
    async def msglb(self, ctx):
        data = self.bot.load_data()
        g = data["guilds"].get(str(ctx.guild.id), {})
        m = g.get("messages", {})

        if not m:
            return await self.bot.sendmessage(ctx, "no data found. go yap something")

        users = sorted(m.items(), key=lambda x: x[1], reverse=True)

        view = MsgLBView(self.bot, ctx, users, per=10)
        embed = view.get_embed()

        await self.bot.sendmessage(ctx, embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(MsgLB(bot))
