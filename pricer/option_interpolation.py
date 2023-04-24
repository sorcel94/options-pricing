from datetime import datetime

class OptionInterpolator:
    def __init__(self, data_source):
        self.data_source = data_source

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
    
    def _find_nearest_lower_upper_strike(self, expiry_strike_data, expiry, target_strike):
        strike_data = sorted(expiry_strike_data[expiry])
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


    def _interpolate_strike_price(self, expiry_strike_data, expiry, target_strike):
        strike_data = expiry_strike_data[expiry]
        lower_strike, upper_strike = self._find_nearest_lower_upper(strike_data, target_strike)

        lower_strike_price = self.data_source[expiry][lower_strike]
        upper_strike_price = self.data_source[expiry][upper_strike]

        interpolated_price = self._interpolate_value(lower_strike, lower_strike_price, upper_strike, upper_strike_price, target_strike)
        return interpolated_price

    def _interpolate_value(self, lower_x, lower_y, upper_x, upper_y, target_x):
        # ... (code to interpolate between the lower and upper values) 
        pass
    
    def linear_interpolation(self, target_strike, target_expiry):
        expiry_strike_data = self._extract_expiry_strike_data()
        
        # Find the nearest lower and upper expiries
        lower_expiry, upper_expiry = self._find_nearest_lower_upper(list(expiry_strike_data.keys()), target_expiry)

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
