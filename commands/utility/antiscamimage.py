from discord.ext import commands


class AntiScam(commands.Cog):
    def __init__(
        self,
        bot
    ):
        self.bot = bot

    @commands.hybrid_command(
        name="antiscamimage",
        description="automatic softban user send crypto scam image (1.jpg, 2.jpg, 3.jpg, 4.jpg)"
    )
    @commands.has_permissions(
        manage_messages=True,
        ban_members=True
    )
    async def antiscamimage(
        self,
        ctx
    ):
        if not ctx.guild:
            return await self.bot.sendmessage(
                ctx,
                "guild only"
            )

        me = ctx.guild.me

        if (
            not me.guild_permissions.ban_members
            or not me.guild_permissions.manage_messages
        ):
            return await self.bot.sendmessage(
                ctx,
                "i need **Manage Messages** and **Ban Members** permissions."
            )

        guilds = (
            self.bot
            .load_data()
            .setdefault(
                "guilds",
                {}
            )
        )

        guild = guilds.setdefault(
            str(ctx.guild.id),
            {}
        )

        antiscam = guild.setdefault(
            "antiscam",
            {}
        )

        antiscam["image"] = not antiscam.get(
            "image",
            False
        )

        await self.bot.save_data()

        await self.bot.sendmessage(
            ctx,
            (
                "enabled"
                if antiscam["image"]
                else "disabled"
            )
        )


async def setup(bot):
    await bot.add_cog(
        AntiScam(bot)
    )