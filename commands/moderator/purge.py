import discord
from discord.ext import commands

class purge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="purge",
        description="delete a number of messages."
    )
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.context, amount: int):

        if amount <= 0:
            return await self.bot.sendmessage(ctx, "amount must be greater than 0.")

        try:
            if ctx.interaction:
                await ctx.interaction.response.defer(ephemeral=True)
            else:
                try:
                    await ctx.message.delete()
                except:
                    pass

            deleted = await ctx.channel.purge(limit=amount)

            msg = f"deleted {len(deleted)} messages."

            if ctx.interaction:
                m = await ctx.interaction.followup.send(msg, ephemeral=True)
            else:
                m = await ctx.send(msg)

            await m.delete(delay=3)

        except discord.forbidden:
            await self.bot.sendmessage(ctx, "i don't have permission to delete messages.")
        except discord.httpexception as e:
            await self.bot.sendmessage(ctx, f"failed to delete messages: {e}")
        except Exception:
            await self.bot.sendmessage(ctx, "something went wrong.")


async def setup(bot):
    await bot.add_cog(purge(bot))
