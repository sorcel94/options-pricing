# Crypto Option Pricer 🚀💰

Welcome to the *Crypto Option Pricer*, a Python library for all your cryptocurrency options pricing needs! Whether you're an experienced quant or just someone who likes to dabble in the world of options, this library will make you feel like you've just discovered buried treasure.

## Features 🌟

* Comprehensive pricing for BTC and ETH options
* Supports market-based pricing using the Deribit API
* Theoretical valuation using the Black-Scholes model and other advanced models
* Clean and optimized code that runs reliably and fast
* Object-oriented design for easy extensibility

## Getting Started 🏁

1. Clone this repository:
git clone https://github.com/yourusername/crypto-option-pricer.git

2. Set up a virtual environment and activate it:
python -m venv venv
source venv/bin/activate

3. Install the required dependencies:
pip install -r requirements.txt

4. Import the library and start pricing those options! 🎉

## Usage 📚

Here's a simple example to get you started:

```python
from crypto_option_pricer import MarketPricer

# Create a MarketPricer instance
pricer = MarketPricer(api_key="your_deribit_api_key", api_secret="your_deribit_api_secret")

# Fetch market data and calculate the option price
option_string = "BTC-25MAR22-20000-C"
price = pricer.compute_price(option_string)

print(f"The computed option price is: {price:.2f}")
```
# Contributing 🤝

Contributors are welcomed! If you'd like to improve the code, add new features, or simply fix a typo, feel free to submit a pull request. Let's make this library the best it can be, together!

License 📄

This project is licensed under the MIT License. See the LICENSE file for more details.