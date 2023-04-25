from datetime import datetime
class OptionInterpolator:
    def __init__(self, data_source, market_pricer):
        self.data_source = data_source
        self.market_pricer = market_pricer

    def _extract_expiry_strike_data(self):
        expiry_strike_data = {}
        for instrument_name in self.data_source:
            expiry, strike = self._parse_instrument_name(instrument_name)
            if expiry not in expiry_strike_data:
                expiry_strike_data[expiry] = []
            expiry_strike_data[expiry].append(strike)
        return expiry_strike_data
    
    def _parse_instrument_name(self, instrument_name):
        instrument_data = instrument_name.split('-')
        strike = float(instrument_data[2])
        expiry = instrument_data[1]
        
        return expiry, strike
    
    def _find_nearest_lower_upper_expiry(self, data, target):
        date_format = "%d%b%y"
        target_date = datetime.strptime(target, date_format)
        lower = None
        upper = None

        for date_str in data:
            date = datetime.strptime(date_str, date_format)

            if date <= target_date:
                if lower is None or date > datetime.strptime(lower, date_format):
                    lower = date_str
            elif date > target_date:
                if upper is None or date < datetime.strptime(upper, date_format):
                    upper = date_str

        return lower, upper
    
    def _find_nearest_lower_upper_strike(self, expiry_strike_data, target_strike):
        strike_data = sorted(expiry_strike_data)
        n = len(strike_data)
        lower = None
        upper = None
        
        # Check if target_strike is outside the strike range
        if target_strike <= strike_data[0]:
            return None, strike_data[0]
        elif target_strike >= strike_data[-1]:
            return strike_data[-1], None
        
        # Binary search for the nearest lower and upper strikes
        left = 0
        right = n - 1
        while left <= right:
            mid = (left + right) // 2
            if strike_data[mid] == target_strike:
                return target_strike, target_strike
            elif strike_data[mid] < target_strike:
                lower = strike_data[mid]
                left = mid + 1
            else:
                upper = strike_data[mid]
                right = mid - 1
        
        return lower, upper

    def _interpolate_strike_price(self, expiry_strike_data, expiry, target_strike, target_instrument, target_quantity, skip_handle_missing_prices=False):
        market_pricer = self.market_pricer
        strike_data = expiry_strike_data[expiry]
        lower_strike, upper_strike = self._find_nearest_lower_upper_strike(strike_data, target_strike)

        if lower_strike == upper_strike:
            contract = '-'.join(target_instrument.split('-')[:2] + [str(lower_strike)] + target_instrument.split('-')[3:])
            data = market_pricer._fetch_option_book(contract)
            bid = market_pricer.calculate_price_if_available(data['bids'], target_quantity)
            ask = market_pricer.calculate_price_if_available(data['asks'], target_quantity)
            bid, ask = market_pricer._handle_missing_prices(bid,ask)
            return {'bid': bid, 'ask': ask}

        target_instrument = target_instrument.split('-')

        target_instrument[2] = str(lower_strike)
        contract_lower = '-'.join(target_instrument)

        target_instrument[2] = str(upper_strike)
        contract_upper = '-'.join(target_instrument)

        lower_data = market_pricer._fetch_option_book(contract_lower)
        upper_data = market_pricer._fetch_option_book(contract_upper)

        lower_bid = market_pricer.calculate_price_if_available(lower_data['bids'], target_quantity)
        lower_ask = market_pricer.calculate_price_if_available(lower_data['asks'], target_quantity)
        upper_bid = market_pricer.calculate_price_if_available(upper_data['bids'], target_quantity)
        upper_ask = market_pricer.calculate_price_if_available(upper_data['asks'], target_quantity)

        if not skip_handle_missing_prices:
            lower_bid, lower_ask = market_pricer._handle_missing_prices(lower_bid, lower_ask, fallback_method=lambda: self._interpolate_strike_price( expiry_strike_data, expiry, target_strike, target_instrument, target_quantity, skip_handle_missing_prices=True ))
            upper_bid, upper_ask = market_pricer._handle_missing_prices(upper_bid, upper_ask, fallback_method=lambda: self._interpolate_strike_price( expiry_strike_data, expiry, target_strike, target_instrument, target_quantity, skip_handle_missing_prices=True ))


        if lower_bid is None and lower_ask is None and upper_bid is None and upper_ask is None:
            raise NotImplementedError("Bid and ask prices missing, theoretical valuation not implemented yet.")

        if lower_bid is None and lower_ask is None:
            interpolated_bid = upper_bid
            interpolated_ask = upper_ask
        elif upper_bid is None and upper_ask is None:
            interpolated_bid = lower_bid
            interpolated_ask = lower_ask
        else:
            interpolated_bid = self._interpolate_value(lower_strike, lower_bid, upper_strike, upper_bid, target_strike)
            interpolated_ask = self._interpolate_value(lower_strike, lower_ask, upper_strike, upper_ask, target_strike)

        return {'bid': interpolated_bid, 'ask': interpolated_ask}

    def _interpolate_value(self, strike1, price1, strike2, price2, target_strike):
        if strike1 == strike2:
            return price1
        return price1 + (target_strike - strike1) * (price2 - price1) / (strike2 - strike1)
    
    def linear_interpolation(self, target_strike, target_expiry):
        expiry_strike_data = self._extract_expiry_strike_data()
        
        # Find the nearest lower and upper expiries
        lower_expiry, upper_expiry = self._find_nearest_lower_upper_expiry(list(expiry_strike_data.keys()), target_expiry)

        # Perform interpolation for each expiry
        lower_expiry_interpolated_price = self._interpolate_strike_price(expiry_strike_data, lower_expiry, target_strike)
        upper_expiry_interpolated_price = self._interpolate_strike_price(expiry_strike_data, upper_expiry, target_strike)

        # Perform interpolation between the lower and upper expiries to get the final interpolated price
        interpolated_price = self._interpolate_value(lower_expiry, lower_expiry_interpolated_price, upper_expiry, upper_expiry_interpolated_price, target_expiry)

        return interpolated_price

    def cubic_spline_interpolation(self, target_strike, target_expiry):
        # Implement cubic spline interpolation using self.data_source
        pass

    def interpolate_option_price(self, target_strike, target_expiry, method='linear'):
        if method == 'linear':
            return self.linear_interpolation(target_strike, target_expiry)
        elif method == 'cubic_spline':
            return self.cubic_spline_interpolation(target_strike, target_expiry)
        else:
            raise ValueError(f"Unsupported interpolation method: {method}")
