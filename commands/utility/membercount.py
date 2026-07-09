from discord.ext import commands
import discord
from datetime import datetime, timedelta, timezone

class MemberCount(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def calc(self, daily, days):
        now = datetime.now(timezone.utc)
        j = l = 0

        for d, s in daily.items():
            dt = datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if dt >= now - timedelta(days=days):
                j += s.get("joins", 0)
                l += s.get("leaves", 0)

        return j, l

    @commands.guild_only()
    @commands.hybrid_command(
        name="membercount",
        description="show member statistics"
    )
    async def membercount(self, ctx):
        guild = ctx.guild

        humans = sum(1 for m in guild.members if not m.bot)
        bots = sum(1 for m in guild.members if m.bot)
        total = guild.member_count

        online = sum(
            1 for m in guild.members
            if not m.bot and m.status in (
                discord.Status.online,
                discord.Status.idle,
                discord.Status.dnd
            )
        )

        data = self.bot.load_data()
        g = data["guilds"].get(str(guild.id), {})
        daily = g.get("joinleave", {}).get("daily", {})

        j1, l1 = self.calc(daily, 1)
        j3, l3 = self.calc(daily, 3)
        j7, l7 = self.calc(daily, 7)
        j14, l14 = self.calc(daily, 14)
        j30, l30 = self.calc(daily, 30)

        embed = discord.Embed(
            title="Member Statistics",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="Current Members",
            value=(
                f"Members: {humans}\n"
                f"Online: {online}\n"
                f"Bots: {bots}\n"
                f"Total: {total}"
            ),
            inline=False
        )

        embed.add_field(
            name="Today (24h)",
            value=f"Joined: {j1}\nLeft: {l1}",
            inline=True
        )

        embed.add_field(
            name="Past 3 Days",
            value=f"Joined: {j3}\nLeft: {l3}",
            inline=True
        )

        embed.add_field(
            name="Past 7 Days",
            value=f"Joined: {j7}\nLeft: {l7}",
            inline=True
        )

        embed.add_field(
            name="Past 14 Days",
            value=f"Joined: {j14}\nLeft: {l14}",
            inline=True
        )

        embed.add_field(
            name="Past 30 Days",
            value=f"Joined: {j30}\nLeft: {l30}",
            inline=True
        )

        await self.bot.sendmessage(ctx, embed=embed)

async def setup(bot):
    await bot.add_cog(MemberCount(bot))
