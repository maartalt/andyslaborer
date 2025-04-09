import asyncio
import logging
import sqlite3
from typing import Optional
import os
from dotenv import load_dotenv

import asqlite
import twitchio
from twitchio.ext import commands
from twitchio import eventsub

from riot_api import RiotAPI

load_dotenv()

LOGGER: logging.Logger = logging.getLogger("Bot")

CLIENT_ID: str = (
    "mbh4ephtc5ejnne0ubxz4wbcstmm6r"  # The CLIENT ID from the Twitch Dev Console
)
CLIENT_SECRET: str = os.getenv(
    "CLIENT_SECRET"
)  # The CLIENT SECRET from the Twitch Dev Console
BOT_ID = "1295589989"  # The Account ID of the bot user...
OWNER_ID = "133404257"  # Your personal User ID..

# Add Riot API constants
RIOT_API_KEY: str = os.getenv("RIOT_API_KEY")  # Get this from developer.riotgames.com
GAME_NAME: str = "maart"  # The riot name to track
TAGLINE: str = "maart"  # The tagline for their Riot ID
REGION: str = "euw1"  # The region of the summoner (e.g., euw1, na1)


class Bot(commands.Bot):
    def __init__(self, *, token_database: asqlite.Pool) -> None:
        self.token_database = token_database
        self.riot_api = RiotAPI(RIOT_API_KEY, REGION)
        self.summoner_puuid: Optional[str] = None
        self.summoner_id: Optional[str] = None
        self.is_in_game = False
        super().__init__(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            bot_id=BOT_ID,
            owner_id=OWNER_ID,
            prefix="!",
        )

    async def setup_hook(self) -> None:
        # Add our component which contains our commands...
        await self.add_component(MyComponent(self))

        # Subscribe to read chat (event_message) from our channel as the bot...
        # This creates and opens a websocket to Twitch EventSub...
        subscription = eventsub.ChatMessageSubscription(
            broadcaster_user_id=OWNER_ID, user_id=BOT_ID
        )
        await self.subscribe_websocket(payload=subscription)

        # Subscribe and listen to when a stream goes live..
        # For this example listen to our own stream...
        subscription = eventsub.StreamOnlineSubscription(broadcaster_user_id=OWNER_ID)
        await self.subscribe_websocket(payload=subscription)

    async def check_game_status(self):
        """Periodically check if summoner is in game."""
        LOGGER.info(f"Starting check_game_status for {GAME_NAME}#{TAGLINE}")
        # First, get summoner ID (only needs to be done once)
        if not self.summoner_id:
            LOGGER.info("No summoner_id found, fetching PUUID...")
            summoner_puuid = await self.riot_api.get_puuid(GAME_NAME, TAGLINE)
            LOGGER.info(f"PUUID response: {summoner_puuid}")
            if not summoner_puuid:
                LOGGER.error(f"Failed to get PUUID for {GAME_NAME}#{TAGLINE}")
                return
            LOGGER.info(
                f"Fetching summoner data using PUUID: {summoner_puuid['puuid']}"
            )
            self.summoner_puuid = summoner_puuid
            summoner_data = await self.riot_api.get_summoner_by_puuid(summoner_puuid)
            LOGGER.info(f"Summoner data response: {summoner_data}")
            if not summoner_data:
                LOGGER.error(f"Could not find summoner: {GAME_NAME, TAGLINE}")
                return

            self.summoner_id = summoner_data["id"]
            LOGGER.info(f"Successfully found summoner_id: {self.summoner_id}")

        while True:
            try:
                game_data = await self.riot_api.get_active_game(self.summoner_id)

                # Player just entered game
                if game_data and not self.is_in_game:
                    self.is_in_game = True
                    LOGGER.info(f"Game started for {GAME_NAME}")
                    channel = self.get_channel(OWNER_ID)
                    if channel:
                        await channel.send("/announce GAME STARTING")

                # Player just finished game
                elif not game_data and self.is_in_game:
                    self.is_in_game = False
                    LOGGER.info(f"Game ended for {GAME_NAME}")

                # Wait 60 seconds before next check
                # Riot API has rate limits, so don't check too frequently
                await asyncio.sleep(60)

            except Exception as e:
                LOGGER.error(f"Error checking game status: {e}")
                await asyncio.sleep(120)  # Wait longer on error

    async def event_ready(self) -> None:
        await super().event_ready()
        LOGGER.info("Successfully logged in as: %s", self.bot_id)

        # Validate Riot API key
        if not await self.riot_api.validate_api_key():
            LOGGER.error("Invalid or expired Riot API key. Please update the key.")
        else:
            LOGGER.info("Riot API key validated successfully")

        # Start the game status checking loop1
        self.loop.create_task(self.check_game_status())

    async def add_token(
        self, token: str, refresh: str
    ) -> twitchio.authentication.ValidateTokenPayload:
        # Make sure to call super() as it will add the tokens interally and return us some data...
        resp: twitchio.authentication.ValidateTokenPayload = await super().add_token(
            token, refresh
        )

        # Store our tokens in a simple SQLite Database when they are authorized...
        query = """
        INSERT INTO tokens (user_id, token, refresh)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            token = excluded.token,
            refresh = excluded.refresh;
        """

        async with self.token_database.acquire() as connection:
            await connection.execute(query, (resp.user_id, token, refresh))

        LOGGER.info("Added token to the database for user: %s", resp.user_id)
        return resp

    async def load_tokens(self, path: str | None = None) -> None:
        # We don't need to call this manually, it is called in .login() from .start() internally...

        async with self.token_database.acquire() as connection:
            rows: list[sqlite3.Row] = await connection.fetchall(
                """SELECT * from tokens"""
            )

        for row in rows:
            await self.add_token(row["token"], row["refresh"])

    async def setup_database(self) -> None:
        # Create our token table, if it doesn't exist..
        query = """CREATE TABLE IF NOT EXISTS tokens(user_id TEXT PRIMARY KEY, token TEXT NOT NULL, refresh TEXT NOT NULL)"""
        async with self.token_database.acquire() as connection:
            await connection.execute(query)

    async def event_ready(self) -> None:
        LOGGER.info("Successfully logged in as: %s", self.bot_id)


class MyComponent(commands.Component):
    def __init__(self, bot: Bot):
        # Passing args is not required...
        # We pass bot here as an example...
        self.bot = bot

    # We use a listener in our Component to display the messages received.
    @commands.Component.listener()
    async def event_message(self, payload: twitchio.ChatMessage) -> None:
        print(f"[{payload.broadcaster.name}] - {payload.chatter.name}: {payload.text}")

    @commands.command()
    async def gamestatus(self, ctx: commands.Context) -> None:
        """Check if player is currently in game."""
        if not self.bot.summoner_id:  # Access through self.bot instead of self
            await ctx.send(f"Could not find summoner: {GAME_NAME}")
            return

        game_data = await self.bot.riot_api.get_active_game(
            self.bot.summoner_id
        )  # Access through self.bot
        if game_data:
            await ctx.send(f"{GAME_NAME} is currently in game!")
        else:
            await ctx.send(f"{GAME_NAME} is not in game")

    @commands.command()
    async def retrievegamestatus(self, ctx: commands.Context) -> None:
        """Check if player is currently in game."""
        try:
            # Get PUUID first
            summoner_puuid = await self.bot.riot_api.get_puuid(GAME_NAME, TAGLINE)
            if not summoner_puuid:
                await ctx.send(f"Could not find Riot ID: {GAME_NAME}#{TAGLINE}")
                return

            # Get summoner data
            summoner_data = await self.bot.riot_api.get_summoner_by_puuid(
                summoner_puuid
            )
            if not summoner_data:
                await ctx.send(
                    f"Could not find summoner data for {GAME_NAME}#{TAGLINE}"
                )
                return

            # Store the summoner_id if we didn't have it before
            if not self.bot.summoner_id:
                self.bot.summoner_id = summoner_data["id"]

            # Check game status
            game_data = await self.bot.riot_api.get_active_game(summoner_puuid)
            if game_data:
                await ctx.send(f"🎮 {GAME_NAME} is currently in game!")
            else:
                await ctx.send(f"⚪ {GAME_NAME} is not in game")

        except Exception as e:
            LOGGER.error(f"Error in gamestatus command: {e}")
            await ctx.send("Error checking game status")

    @commands.Component.listener()
    async def event_stream_online(self, payload: twitchio.StreamOnline) -> None:
        # Event dispatched when a user goes live from the subscription we made above...

        # Keep in mind we are assuming this is for ourselves
        # others may not want your bot randomly sending messages...
        await payload.broadcaster.send_message(
            sender=self.bot.bot_id,
            message=f"Hi... {payload.broadcaster}! You are live!",
        )


def main() -> None:
    twitchio.utils.setup_logging(level=logging.INFO)

    async def runner() -> None:
        async with asqlite.create_pool("tokens.db") as tdb, Bot(
            token_database=tdb
        ) as bot:
            await bot.setup_database()
            await bot.start()

    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Shutting down due to KeyboardInterrupt...")


if __name__ == "__main__":
    main()
