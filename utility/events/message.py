from .stats import update_msg


async def process_image(
    scam_detector,
    message,
    url
):
    try:
        async with scam_detector.http.get(
            url,
            allow_redirects=True
        ) as resp:

            if resp.status != 200:
                return

            content_type = (
                resp.headers.get(
                    "Content-Type",
                    ""
                )
                .lower()
            )

            if not content_type.startswith(
                "image/"
            ):
                return

            image = await resp.read()

            scam_detector.queue.put_nowait(
                (message, image)
            )

    except:
        pass


async def process_embeds(
    scam_detector,
    message
):
    for embed in message.embeds:

        if (
            embed.type == "image"
            and
            embed.url
        ):
            await process_image(
                scam_detector,
                message,
                embed.url
            )

        elif (
            embed.image
            and
            embed.image.url
        ):
            await process_image(
                scam_detector,
                message,
                embed.image.url
            )

        elif (
            embed.thumbnail
            and
            embed.thumbnail.url
        ):
            await process_image(
                scam_detector,
                message,
                embed.thumbnail.url
            )


async def process_raw_urls(
    scam_detector,
    message
):
    for word in message.content.split():

        if not (
            word.startswith(
                "https://"
            )
            or
            word.startswith(
                "http://"
            )
        ):
            continue

        if (
            "media.discordapp.net/"
            not in word
            and
            "cdn.discordapp.com/"
            not in word
        ):
            continue

        await process_image(
            scam_detector,
            message,
            word
        )


async def scan_message(
    bot,
    scam_detector,
    message
):
    if message.author.bot:
        return

    if not message.guild:
        return

    data = bot.load_data()

    g = data["guilds"].get(
        str(message.guild.id),
        {}
    )

    enabled = g.get(
        "antiscam",
        {}
    ).get(
        "image",
        False
    )

    if not enabled:
        return

    if scam_detector.queue.qsize() > 180:
        return

    for attachment in message.attachments:
        try:
            content_type = (
                attachment.content_type
                or
                ""
            ).lower()

            if not content_type.startswith(
                "image/"
            ):
                continue

            image = await attachment.read()

            scam_detector.queue.put_nowait(
                (message, image)
            )

        except:
            pass

    if message.embeds:
        await process_embeds(
            scam_detector,
            message
        )

    await process_raw_urls(
            scam_detector,
            message
        )


async def message_event(
    bot,
    scam_detector,
    message
):
    await scan_message(
        bot,
        scam_detector,
        message
    )
    
    if message.author.bot:
        return
    
    if not message.guild:
        return
    
    await update_msg(
        bot,
        message.guild.id,
        message.author.id
    )


async def message_edit_event(
    bot,
    scam_detector,
    before,
    after
):
    if before.embeds == after.embeds:
        return

    await scan_message(
        bot,
        scam_detector,
        after
    )