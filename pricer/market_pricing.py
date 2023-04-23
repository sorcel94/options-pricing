from option_pricer import OptionPricer
from constants import COIN_GECKO_IDS
import requests
from datetime import datetime, timedelta

class MarketPricer(OptionPricer):
    instruments_cache = {}

    def __init__(self, input_string, quantity, update_cache=True):
        super().__init__()
        self.input_string = input_string
        self.base_url = "https://www.deribit.com/api/v2/"
        self.parse_option_string(input_string, quantity)
        if update_cache:
            self.update_instruments_cache(input_string)
        self.price = self.compute_price()

    def fetch_options_instruments(self):
        url = f"{self.base_url}public/get_book_summary_by_currency?currency={self.option_underlying}&kind=option"
        response = requests.get(url)

        if response.status_code != 200:
            raise requests.exceptions.RequestException(f"Failed to fetch option data from Deribit API: {response.text}")

        book_data = response.json()
        if "result" not in book_data:
            raise ValueError("Unexpected response format from Deribit API")
        
        instrument_names = [entry["instrument_name"] for entry in book_data["result"]]
        return instrument_names

    @classmethod
    def update_instruments_cache(cls, input_string, force_update=False):
        option_underlying = input_string.split("-")[0].upper()

        if option_underlying not in cls.instruments_cache:
            cls.instruments_cache[option_underlying] = {"timestamp": None, "instruments": []}
            
        cache_entry = cls.instruments_cache[option_underlying]
        
        if force_update or cache_entry["timestamp"] is None or datetime.now() - cache_entry["timestamp"] > timedelta(days=1):
            instance = cls(input_string, 1, update_cache=False)
            cache_entry["instruments"] = instance.fetch_options_instruments()
            cache_entry["timestamp"] = datetime.now()

    def fetch_option_book(self):
        # Check if the option is in the cached instruments
        option_name = self.input_string
        if option_name in self.instruments_cache[self.option_underlying]["instruments"]:
            # If the option is available, call the get_order_book endpoint
            url = f"{self.base_url}public/get_order_book?depth=10&instrument_name={option_name}"
            response = requests.get(url)

            if response.status_code != 200:
                raise requests.exceptions.RequestException(f"Failed to fetch option book data from Deribit API: {response.text}")

            order_book_data = response.json()
            return order_book_data['result']
        else:
            # If the option is not available, handle interpolation (to be implemented later)
            raise NotImplementedError("Option not available, interpolation has not been implemented yet.")
    

    def fetch_spot_price(self, currency='usd'):
        coin_id = COIN_GECKO_IDS.get(self.option_underlying)

        if coin_id:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={currency}"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                spot_price = data.get(coin_id, {}).get(currency)
                if spot_price:
                    return spot_price

        # Fallback to Deribit API if CoinGecko fails or asset not found
        url = f"{self.base_url}public/get_index?currency={self.option_underlying}_USDC"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            index_price = data.get("result", {}).get("last_price")
            if index_price:
                return index_price

        # Raise error if both attempts fail
        raise ValueError(f"Failed to fetch spot price for {self.option_underlying}")

    def get_weighted_price(self, use_future_price=True):
        order_book = self.fetch_option_book()
        bids = order_book['bids']
        asks = order_book['asks']
        quantity = self.quantity

        if use_future_price or 'underlying_price' not in order_book:
            underlying_price = order_book['underlying_price']
        else:
            underlying_price = self.fetch_spot_price()
        
        def weighted_price(order_list, target_quantity):
            total_price = 0
            total_qty = 0

            for price, size in order_list:
                if total_qty + size <= target_quantity:
                    total_price += price * size
                    total_qty += size
                else:
                    remaining_qty = target_quantity - total_qty
                    total_price += price * remaining_qty
                    break

            return total_price / target_quantity

        bid_weighted_price = weighted_price(bids, quantity) * underlying_price
        ask_weighted_price = weighted_price(asks, quantity) * underlying_price

        return bid_weighted_price, ask_weighted_price

    
    def get_market_price(self, quantity):
        asset, date_str, strike, option_type = self.parse_option_string(self.input_string)

        option_data = self.fetch_option_data(self.input_string)
        market_price = self.interpolate(strike, option_data, quantity)
        return market_price

    def interpolate(self, target_strike, option_data, quantity):
    # Implement interpolation logic
    # This might involve finding the two closest available strikes in the option_data
    # and computing a weighted average based on their prices and strikes.

    # Assuming the option_data is a list of dictionaries containing 'strike' and 'price' keys
        lower_data = None
        upper_data = None

        for data in option_data:
            strike = data['strike']

            if strike <= target_strike:
                if lower_data is None or strike > lower_data['strike']:
                    lower_data = data
            elif strike > target_strike:
                if upper_data is None or strike < upper_data['strike']:
                    upper_data = data

        if lower_data is None or upper_data is None:
            raise ValueError("Could not find suitable data points for interpolation.")

        lower_weight = (upper_data['strike'] - target_strike) / (upper_data['strike'] - lower_data['strike'])
        upper_weight = 1 - lower_weight
        
        # Calculate the weighted average price considering the quantity
        available_quantity = min(lower_data['amount'], upper_data['amount'])
        if quantity > available_quantity:
            raise ValueError(f"Requested quantity {quantity} exceeds available quantity {available_quantity}.")

        interpolated_price = lower_weight * lower_data['price'] + upper_weight * upper_data['price']

        return interpolated_price
    
    def compute_price(self):
        # Placeholder, will be implemented as last step
        pass

if __name__ == "__main__":
    price = MarketPricer(input_string='BTC-26MAY23-23000-P', quantity=1)
    price.get_weighted_price()