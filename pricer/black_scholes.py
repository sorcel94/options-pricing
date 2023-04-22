from .option_pricer import OptionPricer

class BlackScholesPricer(OptionPricer):
    def __init__(self):
        super().__init__()

    def compute_price(self, ...):
        # Implement Black-Scholes pricing formula
