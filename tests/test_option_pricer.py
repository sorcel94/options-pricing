import unittest
from datetime import datetime
from pricer.option_pricer import OptionPricer

class TestOptionPricerClass(OptionPricer):
    def compute_price(self, *args, **kwargs):
        pass
    
class TestOptionPricer(unittest.TestCase):

    def test_parse_option_string_valid(self):
        pricer = TestOptionPricerClass()
        option_string = "BTC-20SEP23-30000-C"
        asset, date_str, strike, option_type, time_to_expiry = pricer.parse_option_string(option_string)

        self.assertEqual(asset, "BTC")
        self.assertEqual(date_str, "20SEP23")
        self.assertEqual(strike, 30000)
        self.assertEqual(option_type, "call")
        self.assertTrue(time_to_expiry >= 0)


    def test_parse_option_string_invalid(self):
        pricer = TestOptionPricerClass()
        option_string = "BTC-INVALID-30000-C"

        with self.assertRaises(ValueError):
            pricer.parse_option_string(option_string)

    def test_initialize_parameters(self):
        pricer = TestOptionPricerClass()
        pricer.initialize_parameters(strike=30000, time_to_expiry=100, option_type="call", underlying="BTC", quantity=1, interest_rate=0.01)
        
        self.assertEqual(pricer.strike, 30000)
        self.assertEqual(pricer.time_to_expiry, 100)
        self.assertEqual(pricer.option_type, "call")
        self.assertEqual(pricer.option_underlying, "BTC")
        self.assertEqual(pricer.quantity, 1)
        self.assertEqual(pricer.interest_rate, 0.01)

    def test_validate_inputs(self):
        pricer = TestOptionPricerClass()

        # Test valid inputs
        pricer.initialize_parameters(strike=30000, time_to_expiry=100, option_type="call", underlying="BTC", quantity=1, interest_rate=0.01)
        try:
            pricer.validate_inputs()
        except ValueError:
            self.fail("validate_inputs() raised ValueError unexpectedly!")

        # Test invalid inputs
        invalid_inputs = [
            {"strike": -30000, "time_to_expiry": 100, "option_type": "call", "underlying": "BTC", "quantity": 1, "interest_rate": 0.01},
            {"strike": 30000, "time_to_expiry": -100, "option_type": "call", "underlying": "BTC", "quantity": 1, "interest_rate": 0.01},
            {"strike": 30000, "time_to_expiry": 100, "option_type": "invalid", "underlying": "BTC", "quantity": 1, "interest_rate": 0.01},
            {"strike": 30000, "time_to_expiry": 100, "option_type": "call", "underlying": "INVALID", "quantity": 1, "interest_rate": 0.01},
            {"strike": 30000, "time_to_expiry": 100, "option_type": "call", "underlying": "BTC", "quantity": -1, "interest_rate": 0.01},
            {"strike": 30000, "time_to_expiry": 100, "option_type": "call", "underlying": "BTC", "quantity": 1, "interest_rate": -0.01},
        ]

        for inputs in invalid_inputs:
            with self.assertRaises(ValueError):
                pricer.initialize_parameters(**inputs)

if __name__ == "__main__":
    unittest.main()
