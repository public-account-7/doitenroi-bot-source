from datetime import (
    datetime,
    timezone,
    timedelta
)


def get_today():
    return datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%d"
    )


async def update_msg(
    bot,
    gid,
    uid
):
    guilds = (
        bot.load_data()
        .setdefault(
            "guilds",
            {}
        )
    )

    guild = guilds.setdefault(
        str(gid),
        {}
    )

    messages = guild.setdefault(
        "messages",
        {}
    )

    uid = str(uid)

    messages[uid] = (
        messages.get(uid, 0)
        +
        1
    )

    await bot.save_data()


async def update_jl(
    bot,
    gid,
    key
):
    guilds = (
        bot.load_data()
        .setdefault(
            "guilds",
            {}
        )
    )

    guild = guilds.setdefault(
        str(gid),
        {}
    )

    joinleave = guild.setdefault(
        "joinleave",
        {}
    )

    daily = joinleave.setdefault(
        "daily",
        {}
    )

    today = get_today()

    day = daily.setdefault(
        today,
        {
            "joins": 0,
            "leaves": 0
        }
    )

    day[key] = day.get(
        key,
        0
    ) + 1

    now = datetime.now(
        timezone.utc
    )

    cutoff = now - timedelta(days=30)

    for d in list(daily.keys()):
        try:
            dt = datetime.strptime(
                d,
                "%Y-%m-%d"
            ).replace(
                tzinfo=timezone.utc
            )

            if dt < cutoff:
                del daily[d]

        except:
            continue

    await bot.save_data()