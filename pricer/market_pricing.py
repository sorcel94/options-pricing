from .option_pricer import OptionPricer
import requests

class MarketPricer(OptionPricer):
    def __init__(self, base_url="https://www.deribit.com/api/v2/"):
        super().__init__()
        self.base_url = base_url

    def fetch_option_data(self, option_symbol):
        url = f"{self.base_url}public/get_book_summary_by_currency?currency={option_symbol}&kind=option"
        response = requests.get(url)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch option data from Deribit API: {response.text}")

        option_data = response.json()
        return option_data

    def interpolate(self, target_strike, option_data):
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

        interpolated_price = lower_weight * lower_data['price'] + upper_weight * upper_data['price']

        return interpolated_price

