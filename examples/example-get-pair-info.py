from ostium_python_sdk import OstiumSDK
from ostium_python_sdk.config import NetworkConfig
import asyncio


async def main():
    # Initialize SDK
    config = NetworkConfig.testnet()
    sdk = OstiumSDK(config)

    # Get all available pairs
    pairs = await sdk.subgraph.get_pairs()

    print("\nPair Information:")
    print("----------------------------------------")

    for pair in pairs:
        # Get detailed information for each pair from the Graph API
        pair_details = await sdk.subgraph.get_pair_details(pair['id'])
        print("\nPair Details:")
        print("----------------------------------------")
        # Print all available fields in pair_details
        for key, value in pair_details.items():
            print(f"{key}: {value}")
        print("----------------------------------------")


if __name__ == "__main__":
    asyncio.run(main())
