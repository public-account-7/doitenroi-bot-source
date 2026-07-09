from .stats import update_jl


async def member_remove(
    bot,
    member
):
    await update_jl(
        bot,
        member.guild.id,
        "leaves"
    )