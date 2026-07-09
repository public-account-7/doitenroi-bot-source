from discord.ext import commands
import discord

class Msgs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="msgs",
        description="show how much msg u yap in the server"
    )
    async def msgs(self, ctx, member: discord.Member=None):
        member = member or ctx.author

        data = self.bot.load_data()
        g = data["guilds"].get(str(ctx.guild.id), {})
        m = g.get("messages", {})

        uid = str(member.id)
        if uid not in m:
            return await self.bot.sendmessage(ctx,"no data found. go yap something")

        sorted_users = sorted(m.items(), key=lambda x: x[1], reverse=True)
        rank = next((i+1 for i,(u,_) in enumerate(sorted_users) if u == uid), None)

        await self.bot.sendmessage(ctx,
            f"total messages you send: **{m[uid]}**\n"
            f"you are **#{rank}** on the leaderboard"
        )

async def setup(bot):
    await bot.add_cog(Msgs(bot))