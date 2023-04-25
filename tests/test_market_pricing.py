import unittest
from pricer.market_pricing import MarketPricer
from unittest.mock import patch
from datetime import datetime, timedelta

class TestMarketPricerClass(MarketPricer):
    def __init__(self):
        super().__init__()

class TestMarketPricer(unittest.TestCase):

    def test_compute_price(self):
        pricer = TestMarketPricerClass()

        # Test valid inputs
        valid_inputs = {
            'option_data': [("BTC-26MAY23-20000-C", 10)],
            'future_spot': 'future',
            'interpolation_method': 'linear',
            'bid_spread': 0.05,
            'ask_spread': 0.05
        }

        try:
            pricer.compute_price(**valid_inputs)
        except Exception:
            self.fail("compute_price() raised an exception unexpectedly!")

        # Test invalid inputs (should raise ValueError)
        invalid_inputs = {
            'option_data': [("BTC-26MAY23-20000-C", 10), ("invalid")],
            'future_spot': 'future',
            'interpolation_method': 'linear',
            'bid_spread': 0.05,
            'ask_spread': 0.05
        }

        with self.assertRaises(ValueError):
            pricer.compute_price(**invalid_inputs)

    def test_get_weighted_price(self):
        pricer = TestMarketPricerClass()

        # Test valid inputs
        prices = [{"price": 100, "volume": 10}, {"price": 200, "volume": 20}]
        weighted_price = pricer._get_weighted_price(prices)

        self.assertEqual(weighted_price, 166.66666666666666)

        # Test empty input
        with self.assertRaises(ValueError):
            pricer._get_weighted_price([])
    
    def test_update_instruments_cache(self):
        with patch("pricer.market_pricing.MarketPricer._fetch_options_instruments") as mock_fetch_options_instruments:
            # Mock _fetch_options_instruments to return sample data
            mock_fetch_options_instruments.return_value = [
                {
                    "instrument_name": "BTC-20MAY23-20000-C",
                    "bid_price": 1000,
                    "ask_price": 1100,
                    "volume": 20,
                },
                {
                    "instrument_name": "BTC-20MAY23-20000-P",
                    "bid_price": 500,
                    "ask_price": 600,
                    "volume": 10,
                },
            ]

            input_string = "BTC-20MAY23-20000-C"
            TestMarketPricerClass.update_instruments_cache(input_string)

            # Check if cache is updated
            self.assertTrue("BTC" in TestMarketPricerClass.instruments_cache)
            cache_entry = TestMarketPricerClass.instruments_cache["BTC"]
            self.assertIsNotNone(cache_entry["timestamp"])
            self.assertEqual(len(cache_entry["instruments"]), 2)

            # Test forced update
            old_timestamp = cache_entry["timestamp"]
            TestMarketPricerClass.update_instruments_cache(input_string, force_update=True)
            self.assertNotEqual(old_timestamp, TestMarketPricerClass.instruments_cache["BTC"]["timestamp"])

            # Test update with stale data
            old_timestamp = TestMarketPricerClass.instruments_cache["BTC"]["timestamp"]
            TestMarketPricerClass.instruments_cache["BTC"]["timestamp"] -= timedelta(days=2)
            TestMarketPricerClass.update_instruments_cache(input_string)
            self.assertNotEqual(old_timestamp, TestMarketPricerClass.instruments_cache["BTC"]["timestamp"])

            # Test no update if the data is not stale
            old_timestamp = TestMarketPricerClass.instruments_cache["BTC"]["timestamp"]
            TestMarketPricerClass.update_instruments_cache(input_string)
            self.assertEqual(old_timestamp, TestMarketPricerClass.instruments_cache["BTC"]["timestamp"])
    
    def test_validate_inputs(self):
        pricer = TestMarketPricerClass()
        
        # Test valid inputs
        valid_inputs = [
            {'option_data':[("BTC-26MAY23-20000-C", 10)], 'future_spot':'future', 'interpolation_method':'linear', 'bid_spread':0.05, 'ask_spread':0.05},
            {'option_data':[("BTC-26MAY23-20000-C", 10), ("BTC-26MAY23-20000-C", 10)], 'future_spot':'future', 'interpolation_method':'linear', 'bid_spread':0.05, 'ask_spread':0.05}
            
        ]
        for inputs in valid_inputs:
            try:
                pricer._validate_inputs(**inputs)
            except ValueError:
                self.fail("validate_inputs() raised ValueError unexpectedly!")

        # Test invalid inputs
        invalid_inputs = [
            {'option_data':[('invalid')], 'future_spot':'future', 'interpolation_method':'linear', 'bid_spread':0.05, 'ask_spread':0.05},
            {'option_data':[("BTC-26MAY23-20000-C", 10)], 'future_spot':'invalid', 'interpolation_method':'linear', 'bid_spread':0.05, 'ask_spread':0.05},
            {'option_data':[("BTC-26MAY23-20000-C", 10)], 'future_spot':'future', 'interpolation_method':'invalid', 'bid_spread':0.05, 'ask_spread':0.05},
            {'option_data':[("BTC-26MAY23-20000-C", 10)], 'future_spot':'future', 'interpolation_method':'linear', 'bid_spread':-0.05, 'ask_spread':0.05},
            {'option_data':[("BTC-26MAY23-20000-C", 10)], 'future_spot':'future', 'interpolation_method':'linear', 'bid_spread':0.05, 'ask_spread':-0.05},
            {'option_data':[("BTC-26MAY23-20000-C", 10), ("invalid")], 'future_spot':'future', 'interpolation_method':'linear', 'bid_spread':0.05, 'ask_spread':0.05}
        ]

        for inputs in invalid_inputs:
            with self.assertRaises(ValueError):
                pricer._validate_inputs(**inputs)


if __name__ == "__main__":
    unittest.main()
