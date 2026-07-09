from discord.ext import commands

from .events.member_join import member_join
from .events.member_remove import member_remove

from .events.message import (
    message_event,
    message_edit_event
)

from .events.message_delete import message_delete
from .events.message_edit import message_edit

from .events.scam_detect import ScamDetector


class CoreListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.scam_detector = ScamDetector(
            bot
        )

    async def cog_unload(self):
        await self.scam_detector.close()

    @commands.Cog.listener()
    async def on_member_join(
        self,
        member
    ):
        await member_join(
            self.bot,
            member
        )

    @commands.Cog.listener()
    async def on_member_remove(
        self,
        member
    ):
        await member_remove(
            self.bot,
            member
        )

    @commands.Cog.listener()
    async def on_message(
        self,
        message
    ):
        await message_event(
            self.bot,
            self.scam_detector,
            message
        )

    @commands.Cog.listener()
    async def on_message_delete(
        self,
        message
    ):
        await message_delete(
            self.bot,
            message
        )

    @commands.Cog.listener()
    async def on_message_edit(
        self,
        before,
        after
    ):
        await message_edit(
            self.bot,
            before,
            after
        )

        await message_edit_event(
            self.bot,
            self.scam_detector,
            before,
            after
        )


async def setup(bot):
    await bot.add_cog(
        CoreListener(bot)
    )