from .option_pricer import OptionPricer
from .utils import fetch_spot_price
from .constants import COIN_GECKO_IDS
import requests
from datetime import datetime, timedelta
from .option_interpolation import OptionInterpolator

class MarketPricer(OptionPricer):   
    instruments_cache = {}

    def __init__(self):
        super().__init__()
        self.base_url = "https://www.deribit.com/api/v2/"
    
    def __str__(self):
        return f"MarketPricer(input_string='{self.input_string}', quantity={self.quantity})"
    
    @classmethod
    def update_instruments_cache(cls, input_string, force_update=False):
        # Extract the option underlying from the input string
        option_underlying = input_string.split("-")[0].upper()

        # Initialize the cache entry if it does not exist
        if option_underlying not in cls.instruments_cache:
            cls.instruments_cache[option_underlying] = {"timestamp": None, "instruments": []}

        cache_entry = cls.instruments_cache[option_underlying]

        # Update the cache if necessary (forced update or stale data)
        if force_update or cache_entry["timestamp"] is None or datetime.now() - cache_entry["timestamp"] > timedelta(days=1):
            # Create an instance of the class with a quantity of 1 and update_cache set to False to avoid recursion
            instance = cls()
            cache_entry["instruments"] = instance._fetch_options_instruments()
            cache_entry["timestamp"] = datetime.now()

    def _fetch_options_instruments(self):
        # Construct the API request URL
        url = f"{self.base_url}public/get_book_summary_by_currency?currency={self.option_underlying}&kind=option"
        response = requests.get(url)

        # Handle non-successful API response
        if response.status_code != 200:
            raise requests.exceptions.RequestException(f"Failed to fetch option data from Deribit API: {response.text}")

        # Parse the JSON response
        book_data = response.json()
        if "result" not in book_data:
            raise ValueError("Unexpected response format from Deribit API")

        # Extract instrument names from the response
        instrument_names = [entry["instrument_name"] for entry in book_data["result"]]
        return instrument_names

    def _fetch_option_book(self, input_string=None):
        if input_string:
            instrument_name = input_string
        else:
            instrument_name = self.input_string
            
        url = f"{self.base_url}public/get_order_book?depth=1000&instrument_name={instrument_name}"
        response = requests.get(url)

        # Handle non-successful API response
        if response.status_code != 200:
            raise requests.exceptions.RequestException(f"Failed to fetch option book data from Deribit API: {response.text}")

        order_book_data = response.json()
        return order_book_data['result']
        
    def _fetch_spot_price(self, currency='usd'):
        return fetch_spot_price(self.option_underlying, currency=currency, base_url=self.base_url)

    def _get_underlying_price(self, order_book, use_future_price):
        if use_future_price and 'underlying_price' in order_book:
            return order_book['underlying_price']
        else:
            return self._fetch_spot_price()

    def _calculate_price_if_available(self, order_list, target_quantity, underlying_price):
        if order_list:
            return self._weighted_price(order_list, target_quantity) * underlying_price
        else:
            return None
    
    def _weighted_price(self, order_list, target_quantity):
            total_price = 0
            total_qty = 0

            for price, size in order_list:
                if total_qty + size < target_quantity:
                    total_price += price * size
                    total_qty += size
                else:
                    remaining_qty = target_quantity - total_qty
                    total_price += price * remaining_qty
                    total_qty += remaining_qty
                    break
            
            # Handle the case where the remaining quantity is larger than the order book
            if total_qty < target_quantity:
                remaining_qty = target_quantity - total_qty
                total_price += price * remaining_qty
                total_qty += remaining_qty

            return total_price / target_quantity

    def _handle_missing_prices(self, bid_weighted_price, ask_weighted_price, bid_spread=0.05, ask_spread=0.05, fallback_method=None):
        if bid_weighted_price is None and ask_weighted_price is not None:
            bid_weighted_price = ask_weighted_price * (1 - bid_spread)
        elif ask_weighted_price is None and bid_weighted_price is not None:
            ask_weighted_price = bid_weighted_price * (1 + ask_spread)
        elif bid_weighted_price is None and ask_weighted_price is None:
            if fallback_method is not None:
                return fallback_method()
            else:
                raise NotImplementedError("Bid and ask prices missing, interpolation or other methods not implemented yet.")

        return bid_weighted_price, ask_weighted_price

    def _get_weighted_price(self, order_book, use_future_price=True, bid_spread=0.05, ask_spread=0.05):
        bids = order_book['bids']
        asks = order_book['asks']
        quantity = self.quantity

        underlying_price = self._get_underlying_price(order_book, use_future_price)

        bid_weighted_price = self._calculate_price_if_available(bids, quantity, underlying_price)
        ask_weighted_price = self._calculate_price_if_available(asks, quantity, underlying_price)

        bid_weighted_price, ask_weighted_price = self._handle_missing_prices(
            bid_weighted_price, ask_weighted_price, bid_spread, ask_spread)

        return [bid_weighted_price, ask_weighted_price]
    
    def _validate_inputs(self, option_data, future_spot, interpolation_method, bid_spread, ask_spread):
        if future_spot not in ['future', 'spot']:
            raise ValueError("Invalid value for future_spot. Valid values: 'future', 'spot'")
            
        if interpolation_method not in ['linear', 'cubic_spline']:
            raise ValueError("Invalid value for interpolation_method. Valid values: 'linear', 'cubic_spline'")

        if not isinstance(bid_spread, float) or bid_spread <= 0:
            raise ValueError("Invalid value for bid_spread. Must be a positive float value.")

        if not isinstance(ask_spread, float) or ask_spread <= 0:
            raise ValueError("Invalid value for ask_spread. Must be a positive float value.")
        
        if not isinstance(option_data, list):
            raise ValueError("Invalid value for option_data. Must be a list of tuples (option_string, quantity).")

        for option in option_data:
            if not isinstance(option, tuple):
                raise ValueError("Invalid value for option_data. Each element must be a tuple (option_string, quantity).")

    def _process_option(self, option_tuple, future_spot, interpolation_method, bid_spread, ask_spread, update_cache, verbose):
        input_string, quantity = option_tuple
        self.parse_option_string(input_string, quantity)
        if update_cache:
            self.update_instruments_cache(input_string)

        option_name = self.input_string
        if option_name in self.instruments_cache[self.option_underlying]["instruments"]:
            if verbose:
                print(f"Fetching order book for {option_name}...")
            order_book = self._fetch_option_book()
        else:
            if verbose:
                print(f"Option {option_name} not available. Using interpolation method: {interpolation_method}...")

            instrument_data = option_name.split('-')
            target_strike = float(instrument_data[2])
            target_expiry = instrument_data[1]
            target_quantity = self.quantity

            interpolator = OptionInterpolator(self.instruments_cache[self.option_underlying]['instruments'], self)
            interpolated_price = interpolator.interpolate_option_price(target_strike, target_expiry, target_quantity, method=interpolation_method)
            return interpolated_price

        if verbose:
            print("Using spot price..." if future_spot == 'spot' else "Using future price...")
        price = self._get_weighted_price(order_book, use_future_price=(future_spot == 'future'), bid_spread=bid_spread, ask_spread=ask_spread)
        return price
    
    def compute_price(self, option_data, future_spot='future', interpolation_method='linear', bid_spread=0.05, ask_spread=0.05, update_cache=True, verbose=True):
        """
        Compute the option price using weighted prices from the order book or interpolation.

        Parameters
        ----------
        option_data : list of tpl [(input_opt , quantity)]
            the list of options to be priced, the sintax of the input_option is ASSET-DDMMMYY-STRIKE-K
            where:  ASSET -> crypto ticker eg. BTC,ETH
                    DDMMMYY -> string date eg. 20SEP23
                    STRIKE -> strike price wanted eg. 200 (it can be a float 200.1)
                    K -> option type, eg. C (call) or P (put)
            Valid value: eg. BTC-20SEP23-30000-C
            
        future_spot : str, optional, default: 'future'
            Whether to use the future price ('future') or spot price ('spot') for the underlying asset.
            Valid values: 'future', 'spot'

        interpolation_method : str, optional, default: 'linear'
            The method to use for price interpolation if the option is not available in the order book.
            Valid values: 'linear', 'cubic_spline'

        bid_spread : float, optional, default: 0.05
            The spread to apply when calculating bid price if only the ask price is available.
            Must be a positive float value.

        ask_spread : float, optional, default: 0.05
            The spread to apply when calculating ask price if only the bid price is available.
            Must be a positive float value.

        Returns
        -------
        price : float
            The computed price for the option.

        Raises
        ------
        NotImplementedError
            If method is not implemented yet.
        """
        self._validate_inputs(option_data, future_spot, interpolation_method, bid_spread, ask_spread)
    
        price_dic = {}
        for option_tuple in option_data:
            price_dic[option_tuple[0]] = self._process_option(option_tuple, future_spot, interpolation_method, bid_spread, ask_spread, update_cache, verbose)

        return price_dic


if __name__ == "__main__":
    price = MarketPricer(input_string='BTC-29MAY23-28000-C', quantity=10, verbose=True)
    weighted_price = price.compute_price()
    print(weighted_price)
    