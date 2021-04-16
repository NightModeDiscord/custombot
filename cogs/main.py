import asyncio
import re

from discord import Embed, RawReactionActionEvent, TextChannel
from discord.ext.commands import Bot, Cog, Context, command, is_owner


class Main(Cog):
    def __init__(self, bot: Bot, *, channel_id: int):
        self.bot = bot
        self.channel_id = channel_id
        self.ACCEPT_EMOJI = "\u2705"

    @property
    def channel(self) -> TextChannel:
        channel = self.bot.get_channel(self.channel_id)
        if not isinstance(channel, TextChannel):
            raise RuntimeError("Invalid channel_id configured.")
        return channel

    @command(name="ssl")
    async def ssl(self, ctx: Context):
        embed = Embed(
            title="Choose",
            description=(
                "Choose type of verification\n"
                ":one: report server server\n"
                ":two: for company verification"
            ),
        )
        m = await ctx.send(embed=embed)
        EMOJIS = ("1\ufe0f\u20e3", "2\ufe0f\u20e3")
        for e in EMOJIS:
            await m.add_reaction(e)

        try:
            r, _ = await self.bot.wait_for(
                "reaction_add",
                check=lambda r, u: u == ctx.author
                and r.message == m
                and r.emoji in EMOJIS,
            )
        except asyncio.TimeoutError:
            return await ctx.send("Cancelled!")

        if r.emoji == EMOJIS[0]:
            await self.report(ctx)
        else:
            await self.verify(ctx)

    async def report(self, ctx: Context):
        await ctx.send("Send the permanent invite to the server you're reporting")
        try:
            m = await self.bot.wait_for(
                "message",
                check=lambda m: ctx.channel == m.channel and m.author == ctx.author,
                timeout=60,
            )
        except asyncio.TimeoutError:
            return ctx.send("Timeout!")

        invite = m.content
        result = re.search(
            r"https://discord.gg/[a-z0-9]{10}", invite, flags=re.IGNORECASE
        )
        print(result)
        if not result:
            return await ctx.send("No invite found!")
        invite = result.string

        embed = Embed(title="Report")
        embed.set_author(name=ctx.author.name, icon_url=str(ctx.author.avatar_url))

        embed.add_field(name="Invite", value=invite)
        files = await self.get_attachments(ctx)
        if not files:
            return
        embed.add_field(name="Attachments", value=files)

        # TODO Send in a channel, save to db
        m = await self.channel.send(embed=embed)
        await ctx.send("Successfully reported!")

    async def verify(self, ctx: Context):
        files = await self.get_attachments(ctx)
        if not files:
            return

        embed = Embed(title="Verification")
        embed.add_field(name="Attachments", value=files)

        m = await self.channel.send(embed=embed)
        await m.add_reaction(self.ACCEPT_EMOJI)
        await ctx.send("Successfully requested!")

    async def get_attachments(self, ctx: Context):
        await ctx.send("Send proofs as **attachments**")
        try:
            m = await self.bot.wait_for(
                "message",
                check=lambda m: ctx.channel == m.channel and m.author == ctx.author,
                timeout=60,
            )
        except asyncio.TimeoutError:
            await ctx.send("Timeout!")
            return
        if not m.attachments:
            await ctx.send("No attachments found!")
            return
        return "\n".join([f"[{a.filename}]({a.url})" for a in m.attachments])

    @Cog.listener("on_raw_reaction_add")
    async def confirm(self, payload: RawReactionActionEvent):
        if payload.channel_id != self.channel_id:
            return
        if str(payload.emoji) != self.ACCEPT_EMOJI:
            return

        msg = await self.channel.fetch_message(payload.message_id)

        # TODO: Create an image and send
        # $wip

    @command()
    @is_owner()
    async def rl(self, ctx: Context):
        self.bot.reload_extension("cogs.main")
        await ctx.send("Done.")


def setup(bot):
    bot.add_cog(Main(bot, channel_id=770952819570245632))
