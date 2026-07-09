import discord
from discord.ext import commands


async def safe_delete(message):
    try:
        await message.delete()
    except (discord.Forbidden, discord.NotFound):
        pass


class Say(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="say",
        description="Make the bot say something."
    )
    async def say(self, ctx, *, text: str):

        if ctx.interaction is None and ctx.message:
            await safe_delete(ctx.message)

        user_perms = ctx.channel.permissions_for(ctx.author)
        bot_perms = ctx.channel.permissions_for(ctx.guild.me)

        allow_embed = user_perms.embed_links and bot_perms.embed_links

        await ctx.send(
            text,
            suppress_embeds=not allow_embed,
            allowed_mentions=discord.AllowedMentions.none()
        )


async def setup(bot):
    await bot.add_cog(Say(bot))