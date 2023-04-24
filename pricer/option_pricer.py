from abc import ABC, abstractmethod
from datetime import datetime

class OptionPricer(ABC):
    def __init__(self):
        # Common attributes for all pricing models
        self.strike = None
        self.time_to_expiry = None
        self.option_type = None
        self.interest_rate = None
        self.option_underlying = None
        self.quantity = None

    def initialize_parameters(self, strike, time_to_expiry, option_type, underlying, quantity, interest_rate=None):
        # Set the common parameters for all pricing models
        self.strike = strike
        self.time_to_expiry = time_to_expiry
        self.option_type = option_type
        self.interest_rate = interest_rate if interest_rate is not None else 0
        self.option_underlying = underlying
        self.quantity = quantity

        self.validate_inputs()

    def validate_inputs(self):
        # Validate input parameters to ensure they meet the required conditions
        if self.strike <= 0:
            raise ValueError("Strike price must be positive.")
        if self.time_to_expiry < 0:
            raise ValueError("Time to expiry must be positive.")
        if self.option_type not in ['call', 'put']:
            raise ValueError("Option type must be either 'call' or 'put'.")
        if self.interest_rate < 0:
            raise ValueError("Interest rate must be non-negative.")
        if self.option_underlying not in ['BTC', 'ETH']:
            raise ValueError("Option underlying must be either 'BTC' or 'ETH'. Other underlyings not yet implemented.")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive.")
    
    def parse_option_string(self, option_string, quantity=1, interest_rate=None):
        # Parse the option string and initialize the common parameters
        asset, date_str, strike_str, option_kind = option_string.split("-")
        strike = float(strike_str)
        asset = asset.upper()
        expiration_date = datetime.strptime(date_str, "%d%b%y")
        time_to_expiry = (expiration_date - datetime.now()).days
        option_type = "call" if option_kind == "C" else "put"
        
        self.initialize_parameters(strike=strike, time_to_expiry=time_to_expiry,
                                option_type=option_type, underlying=asset, quantity=quantity, interest_rate=interest_rate)

        return asset, date_str, strike, option_type, time_to_expiry

    # The compute_price method must be implemented by all derived classes
    @abstractmethod
    def compute_price(self, *args, **kwargs):
        pass
