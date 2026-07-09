import discord
from discord.ext import commands
from discord import app_commands

class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="serverinfo",
        description="Show detailed server information"
    )
    async def serverinfo(self, ctx: commands.Context):
        guild = ctx.guild
        if guild is None:
            return await self.bot.sendmessage(ctx, "This command can only be used in a server.")

        created_at = int(guild.created_at.timestamp())

        humans = sum(not m.bot for m in guild.members)
        bots = sum(m.bot for m in guild.members)
        online = sum(m.status != discord.Status.offline for m in guild.members)

        verification_map = {
            discord.VerificationLevel.none: "None",
            discord.VerificationLevel.low: "Low",
            discord.VerificationLevel.medium: "Medium",
            discord.VerificationLevel.high: "High",
            discord.VerificationLevel.highest: "Very High"
        }

        mfa_map = {
            discord.MFALevel.disabled: "Disabled",
            discord.MFALevel.require_2fa: "Enabled"
        }

        verification = verification_map.get(guild.verification_level, str(guild.verification_level))
        mfa = mfa_map.get(guild.mfa_level, str(guild.mfa_level))

        embed = discord.Embed(
            title=guild.name,
            color=discord.Color.blurple()
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        if guild.banner:
            embed.set_image(url=guild.banner.url)

        embed.add_field(
            name="Owner",
            value=f"{guild.owner} ({guild.owner_id})",
            inline=False
        )

        embed.add_field(
            name="Members",
            value=f"Total: {guild.member_count}\nHumans: {humans}\nBots: {bots}\nOnline: {online}",
            inline=True
        )

        embed.add_field(
            name="Channels",
            value=f"Text: {len(guild.text_channels)}\nVoice: {len(guild.voice_channels)}\nStage: {len(guild.stage_channels)}",
            inline=True
        )

        embed.add_field(
            name="Counts",
            value=f"Roles: {len(guild.roles)}\nEmojis: {len(guild.emojis)}\nStickers: {len(guild.stickers)}",
            inline=True
        )

        embed.add_field(
            name="Boost",
            value=f"Level: {guild.premium_tier}\nBoosts: {guild.premium_subscription_count}",
            inline=True
        )

        embed.add_field(
            name="Security",
            value=f"Verification: {verification}\n2FA: {mfa}",
            inline=True
        )

        embed.add_field(
            name="Created",
            value=f"<t:{created_at}:F>\n<t:{created_at}:R>",
            inline=False
        )

        media = []

        if guild.icon:
            media.append(f"Avatar: [Click Me]({guild.icon.url})")

        if guild.banner:
            media.append(f"Banner: [Click Me]({guild.banner.url})")

        if media:
            embed.add_field(
                name="Media",
                value="\n".join(media),
                inline=False
            )

        if guild.vanity_url_code:
            embed.add_field(
                name="Vanity URL",
                value=f"https://discord.gg/{guild.vanity_url_code}",
                inline=False
            )

        if guild.description:
            embed.description = guild.description[:4096]

        embed.set_footer(text=f"ID: {guild.id}")

        await self.bot.sendmessage(ctx, embed=embed)

async def setup(bot):
    await bot.add_cog(ServerInfo(bot))