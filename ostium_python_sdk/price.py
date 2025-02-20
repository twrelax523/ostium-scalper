import aiohttp
from typing import Tuple


class Price:
    def __init__(self):
        self.base_url = "https://listener.ostium.io"

    # Returns a list of price data, e.g: [{'feed_id': '0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8', 'bid': 97241.43864211132, 'mid': 97243.36503172085, 'ask': 97245.2739217016, 'isMarketOpen': True, 'from': 'BTC', 'to': 'USD', 'timestampSeconds': 1740043714}, ...]
    async def get_latest_prices(self):
        """
        Fetches the latest prices from the Ostium price listener service.
        Returns a dictionary of price data.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/PricePublish/latest-prices") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(
                        f"Failed to fetch prices: {response.status}")

    # Returns a json, e.g: {'feed_id': '0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8', 'bid': 97241.43864211132, 'mid': 97243.36503172085, 'ask': 97245.2739217016, 'isMarketOpen': True, 'from': 'BTC', 'to': 'USD', 'timestampSeconds': 1740043714}
    async def get_latest_price_json(self, from_asset: str, to_asset: str) -> Tuple[float, bool]:
        prices = await self.get_latest_prices()
        for price_data in prices:
            if (price_data.get('from') == from_asset and
                    price_data.get('to') == to_asset):
                print(f"get_latest_price_json: {price_data}")
                return price_data
        raise ValueError(f"No price found for pair: {from_asset}/{to_asset}")

    # Returns a mid price and isMarketOpen tuple, e.g: (97243.36503172085, True)
    async def get_price(self, from_asset: str, to_asset: str) -> Tuple[float, bool]:
        """
        Get the latest price and market status for a specific asset pair.
        Args:
            from_asset: The base asset symbol (e.g., "BTC")
            to_asset: The quote asset symbol (e.g., "USD")
        Returns:
            Tuple[float, bool]: The latest price and market open status for the asset pair
        """
        prices = await self.get_latest_prices()
        for price_data in prices:
            if (price_data.get('from') == from_asset and
                    price_data.get('to') == to_asset):
                return float(price_data.get('mid', 0)), price_data.get('isMarketOpen', False)
        raise ValueError(f"No price found for pair: {from_asset}/{to_asset}")
