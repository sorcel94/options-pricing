import requests
from constants import COIN_GECKO_IDS

def fetch_spot_price(option_underlying, currency='usd', base_url="https://www.deribit.com/api/v2/"):
    coin_id = COIN_GECKO_IDS.get(option_underlying)

    if coin_id:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={currency}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            spot_price = data.get(coin_id, {}).get(currency)
            if spot_price:
                return spot_price

    # Fallback to Deribit API if CoinGecko fails or asset not found
    url = f"{base_url}public/get_index?currency={option_underlying}_USDC"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        index_price = data.get("result", {}).get("last_price")
        if index_price:
            return index_price

    # Raise error if both attempts fail
    raise ValueError(f"Failed to fetch spot price for {option_underlying}")
