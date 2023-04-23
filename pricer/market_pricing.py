from .option_pricer import OptionPricer
import requests
from datetime import datetime, timedelta

class MarketPricer(OptionPricer):
    instruments_cache = {}  

    def __init__(self, input_string, base_url="https://www.deribit.com/api/v2/"):
        super().__init__()
        self.base_url = base_url
        self.input_string = input_string
        self.parse_option_string(input_string)
        self.update_instruments_cache(input_string)

    def fetch_options_instruments(self):
        url = f"{self.base_url}public/get_book_summary_by_currency?currency={self.option_underlying}&kind=option"
        response = requests.get(url)

        if response.status_code != 200:
            raise requests.exceptions.RequestException(f"Failed to fetch option data from Deribit API: {response.text}")

        book_data = response.json()
        instrument_names = [entry["instrument_name"] for entry in book_data["result"]]
        return instrument_names

    @classmethod
    def update_instruments_cache(cls, input_string, force_update=False):
        option_underlying = input_string.split("-")[0].upper()

        if option_underlying not in cls.instruments_cache:
            cls.instruments_cache[option_underlying] = {"timestamp": None, "instruments": []}

        cache_entry = cls.instruments_cache[option_underlying]

        if force_update or cache_entry["timestamp"] is None or datetime.now() - cache_entry["timestamp"] > timedelta(days=1):
            instance = cls(input_string)  # Create an instance with the user's input string to fetch instruments
            cache_entry["instruments"] = instance.fetch_options_instruments()
            cache_entry["timestamp"] = datetime.now()

    def fetch_option_book(self):
        pass
    
    def get_weighted_price(self, quantity):
        # Check if the option is available in the instruments cache
        if self.input_string not in self.instruments_cache["instruments"]:
            raise ValueError("Requested option is not available.")

        # Fetch the option book for the given option
        option_book = self.fetch_option_book()

        # Compute the weighted price based on the quantity
        # implement the logic for calculating the weighted price based on the option book data and the given quantity
        # ...

        return weighted_price
    
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

