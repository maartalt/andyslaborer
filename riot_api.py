import aiohttp
import logging
from typing import Optional

LOGGER: logging.Logger = logging.getLogger("RiotAPI")


class RiotAPI:
    def __init__(self, api_key: str, region: str = "euw1"):
        self.api_key = api_key
        self.region = region
        self.headers = {"X-Riot-Token": api_key}
        LOGGER.info(f"RiotAPI initialized with region: {region}")
        # Base URLs
        self.base_urls = {
            "euw1": "https://europe.api.riotgames.com",
            "na1": "https://americas.api.riotgames.com",
            # Add other regions as needed
        }

    async def validate_api_key(self) -> bool:
        """Validate if the API key is working."""
        url = f"{self.base_urls[self.region]}/riot/account/v1/accounts/by-riot-id/test/NA1"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 403:
                        LOGGER.error("API Key is invalid or expired")
                        return False
                    return True
        except Exception as e:
            LOGGER.error(f"Error validating API key: {e}")
            return False

    async def get_puuid(self, game_name: str, tag_line: str) -> Optional[str]:
        """Get PUUID from Riot ID (game name + tagline)."""
        url = f"{self.base_urls[self.region]}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"

        LOGGER.info("=" * 50)
        LOGGER.info(f"Getting PUUID for {game_name}#{tag_line}")
        LOGGER.info(f"Request URL: {url}")
        LOGGER.info(
            f"Using API key: {self.api_key[:10]}..."
        )  # Only show first 10 chars

        try:
            async with aiohttp.ClientSession() as session:
                LOGGER.info("Making API request...")
                async with session.get(url, headers=self.headers) as response:
                    response_text = await response.text()
                    LOGGER.info(f"Response status: {response.status}")
                    LOGGER.info(f"Response body: {response_text}")

                    if response.status == 200:
                        data = await response.json()
                        puuid = data.get("puuid")
                        LOGGER.info(f"Successfully got PUUID: {puuid}")
                        return puuid
                    elif response.status == 403:
                        LOGGER.error("API Key is invalid or expired")
                        return None
                    elif response.status == 404:
                        LOGGER.error(f"Summoner {game_name}#{tag_line} not found")
                        return None
                    else:
                        LOGGER.error(f"Unexpected status code: {response.status}")
                        return None
        except Exception as e:
            LOGGER.error(f"Exception in get_puuid: {str(e)}", exc_info=True)
            return None
        finally:
            LOGGER.info("=" * 50)

    async def get_summoner_by_puuid(self, puuid: str) -> Optional[dict]:
        """Get summoner info by PUUID."""
        url = f"https://{self.region}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"

        LOGGER.info("=" * 50)
        LOGGER.info(f"Getting summoner data for PUUID: {puuid}")
        LOGGER.info(f"Request URL: {url}")

        try:
            async with aiohttp.ClientSession() as session:
                LOGGER.info("Making API request...")
                async with session.get(url, headers=self.headers) as response:
                    response_text = await response.text()
                    LOGGER.info(f"Response status: {response.status}")
                    LOGGER.info(f"Response body: {response_text}")

                    if response.status == 200:
                        data = await response.json()
                        LOGGER.info(f"Successfully got summoner data: {data}")
                        return data
                    else:
                        LOGGER.error(f"Error getting summoner data: {response.status}")
                        return None
        except Exception as e:
            LOGGER.error(f"Exception in get_summoner_by_puuid: {str(e)}", exc_info=True)
            return None
        finally:
            LOGGER.info("=" * 50)

    async def get_active_game(self, summoner_puuid: str) -> Optional[dict]:
        """Check if summoner is in active game."""
        url = f"https://{self.region}.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{summoner_puuid}"

        LOGGER.info("=" * 50)
        LOGGER.info(f"Checking active game for summoner PUUID: {summoner_puuid}")
        LOGGER.info(f"Request URL: {url}")

        try:
            async with aiohttp.ClientSession() as session:
                LOGGER.info("Making API request...")
                async with session.get(url, headers=self.headers) as response:
                    response_text = await response.text()
                    LOGGER.info(f"Response status: {response.status}")
                    LOGGER.info(f"Response body: {response_text}")

                    if response.status == 200:
                        data = await response.json()
                        LOGGER.info("Found active game")
                        return data
                    elif response.status == 404:
                        LOGGER.info("No active game found")
                        return None
                    else:
                        LOGGER.error(f"Error checking game status: {response.status}")
                        return None
        except Exception as e:
            LOGGER.error(f"Exception in get_active_game: {str(e)}", exc_info=True)
            return None
        finally:
            LOGGER.info("=" * 50)
