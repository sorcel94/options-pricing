class OptionPricer:
    def __init__(self):
        self.underlying_price = None
        self.strike = None
        self.time_to_expiry = None
        self.option_type = None
        self.interest_rate = None

    def initialize_parameters(self, underlying_price, strike, time_to_expiry, option_type, interest_rate=None):
        self.underlying_price = underlying_price
        self.strike = strike
        self.time_to_expiry = time_to_expiry
        self.option_type = option_type
        self.interest_rate = interest_rate if interest_rate is not None else 0

        self.validate_inputs()

    def compute_price(self):
        raise NotImplementedError("The 'compute_price' method should be implemented in each child class.")

    def validate_inputs(self):
        if self.underlying_price <= 0:
            raise ValueError("Underlying price must be positive.")
        if self.strike <= 0:
            raise ValueError("Strike price must be positive.")
        if self.time_to_expiry <= 0:
            raise ValueError("Time to expiry must be positive.")
        if self.option_type not in ['call', 'put']:
            raise ValueError("Option type must be either 'call' or 'put'.")
        if self.interest_rate < 0:
            raise ValueError("Interest rate must be non-negative.")
