import re
import traceback
from typing import Iterable

from aiohttp import ClientSession
from discord import AllowedMentions, Color, Embed, Intents, Message
from discord.ext import commands
from discord.http import HTTPClient


class Bot(commands.Bot):
    http: HTTPClient

    def __init__(self, *, load_extensions=True, loadjsk=True):
        allowed_mentions = AllowedMentions(
            users=True, replied_user=True, roles=False, everyone=False
        )
        super().__init__(
            command_prefix="t ",
            intents=Intents.all(),
            allowed_mentions=allowed_mentions,
        )

        if load_extensions:
            self.load_extensions(("cogs.main",))
        if loadjsk:
            self.load_extension("jishaku")

    @property
    def session(self) -> ClientSession:
        return self.http._HTTPClient__session  # type: ignore

    def load_extensions(self, extentions: Iterable[str]):
        for ext in extentions:
            try:
                self.load_extension(ext)
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)

    async def on_message(self, msg: Message):
        if msg.author.bot:
            return
        await self.process_commands(msg)

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.CommandInvokeError):
            embed = Embed(
                title="Error",
                description="An unknown error has occurred and my developer has been notified of it.",
                color=Color.red(),
            )
            await ctx.send(embed=embed)

            traceback_text = "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )
            print(traceback_text)

        title = " ".join(re.compile(r"[A-Z][a-z]*").findall(error.__class__.__name__))
        await ctx.send(
            embed=Embed(title=title, description=str(error), color=Color.red())
        )

    async def on_ready(self):
        print("Ready!")


if __name__ == "__main__":
    import os

    try:
        import dotenv
    except ImportError:
        pass
    else:
        dotenv.load_dotenv(".env")

    os.environ.setdefault("JISHAKU_HIDE", "1")
    os.environ.setdefault("JISHAKU_RETAIN", "1")
    os.environ.setdefault("JISHAKU_NO_UNDERSCORE", "1")

    bot = Bot()
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("No token set.")
    bot.run(token)
