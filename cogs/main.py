import asyncio
import io
from typing import Tuple

from discord import Embed, File, Invite, RawReactionActionEvent, TextChannel
from discord.ext.commands import (
    Bot,
    Cog,
    CommandError,
    Context,
    InviteConverter,
    command,
    is_owner,
)
from PIL import Image, ImageDraw, ImageFont


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
                "Choose Option\n"
                ":one: report server\n"
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

        embed = Embed(title="Report")
        embed.set_author(name=ctx.author.name, icon_url=str(ctx.author.avatar_url))

        embed.add_field(name="Invite", value=(await self.get_invite(ctx)).url)
        files = await self.get_attachments(ctx)
        embed.add_field(name="Attachments", value=files)

        await self.channel.send(embed=embed)
        await ctx.send("Successfully reported!")

    async def verify(self, ctx: Context):

        embed = Embed(title="Verification")
        embed.add_field(name="Invite", value=(await self.get_invite(ctx)).url)
        embed.add_field(name="Attachments", value=await self.get_attachments(ctx))

        m = await self.channel.send(embed=embed)
        await m.add_reaction(self.ACCEPT_EMOJI)
        await ctx.send("Successfully submitted!")

    async def get_invite(self, ctx) -> Invite:
        await ctx.send("Send the permanent invite to the server")
        try:
            m = await self.bot.wait_for(
                "message",
                check=lambda m: ctx.channel == m.channel and m.author == ctx.author,
                timeout=60,
            )
        except asyncio.TimeoutError:
            raise CommandError("Timeout!")
        return await InviteConverter().convert(ctx, m.content)

    async def get_attachments(self, ctx: Context) -> str:
        await ctx.send("Send proofs as **attachments**")
        try:
            m = await self.bot.wait_for(
                "message",
                check=lambda m: ctx.channel == m.channel and m.author == ctx.author,
                timeout=60,
            )
        except asyncio.TimeoutError:
            raise CommandError("Timeout!")
        if not m.attachments:
            raise CommandError("No files found!")
        return "\n".join([f"[{a.filename}]({a.url})" for a in m.attachments])

    @Cog.listener("on_raw_reaction_add")
    async def confirm(self, payload: RawReactionActionEvent):
        if payload.channel_id != self.channel_id:
            return
        if str(payload.emoji) != self.ACCEPT_EMOJI:
            return

        msg = await self.channel.fetch_message(payload.message_id)

        if msg.author != self.bot.user:
            return
        if payload.member and payload.member.bot:
            return

        embed = msg.embeds[0]
        if embed.title != "Verification":
            return
        invite: Invite = await InviteConverter().convert(await self.bot.get_context(msg), embed.fields[0].value)  # type: ignore

        f = self.draw(
            (str(invite.inviter), (480, 200)),
            ("Scam proof", (223, 324)),
            (str(invite.guild.id), (223, 379)),
        )

        try:
            await invite.inviter.send(file=File(f, filename="certificate.jpg"))
        except:
            await self.channel.send(
                "Unable to DM applier, sending here.",
                file=File(f, filename="certificate.jpg"),
            )

    @staticmethod
    def draw(*draws: Tuple[str, Tuple[int, int]]):
        font = ImageFont.truetype("OpenSans-Light.ttf", size=40)
        img = Image.open("certificate.jpg")
        imgdraw = ImageDraw.Draw(img)
        for text, coord in draws:
            imgdraw.text(coord, text, fill=(0, 0, 0), font=font)

        b = io.BytesIO()
        img.save(b, format="JPEG")
        b.seek(0)
        return b

    @command()
    @is_owner()
    async def rl(self, ctx: Context):
        self.bot.reload_extension("cogs.main")
        await ctx.send("Done.")


def setup(bot):
    # bot.add_cog(Main(bot, channel_id=828282130538823750))
    bot.add_cog(Main(bot, channel_id=789838528271745045))
