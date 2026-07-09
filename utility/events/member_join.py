from .stats import update_jl


async def member_join(
    bot,
    member
):
    await update_jl(
        bot,
        member.guild.id,
        "joins"
    )