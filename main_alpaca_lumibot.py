import pandas as pd
from backtesting import Backtest, Strategy
import numpy as np
from datetime import datetime, timedelta
from lumibot.backtesting import YahooDataBacktesting
from lumibot.credentials import IS_BACKTESTING
from lumibot.strategies import Strategy
from lumibot.traders import Trader
import numpy as np
import pandas as pd


class Trend(Strategy):
    parameters = {
        "symbol" : "GLD",
        "quantity" : None
    }

    def initialize(self):
        self.vars.signal = None
        self.vars.start = "2023-01-01"
        self.sleeptime = "1D"
    
    def on_trading_iteration(self):

        bars = self.get_historical_prices(self.parameters['symbol'], 22, "day")
        gld = bars.df
        gld['9-day'] = gld['close'].rolling(9).mean()
        gld['21-day'] = gld['close'].rolling(21).mean()
        gld['Signal'] = np.where(np.logical_and(gld['9-day'] > gld['21-day'],
                                                gld['9-day'].shift(1) < gld['21-day'].shift(1)),
                                 "BUY", None)
        gld['Signal'] = np.where(np.logical_and(gld['9-day'] < gld['21-day'],
                                                gld['9-day'].shift(1) > gld['21-day'].shift(1)),
                                 "SELL", gld['Signal'])
        self.vars.signal = gld.iloc[-1].Signal
        
        symbol = self.parameters['symbol']
        price = self.get_last_price(symbol)
        cash = self.get_cash()
        quantity = cash * .5 // price
        if self.vars.signal == 'BUY':
            pos = self.get_position(symbol)
            if pos:
                self.sell_all()
                
            order = self.create_order(symbol, quantity, "buy")
            self.submit_order(order)

        elif self.vars.signal == 'SELL':
            pos = self.get_position(symbol)
            if pos:
                self.sell_all()
            cash = self.get_cash()
            quantity = cash * .5 // price    
            order = self.create_order(symbol, quantity, "sell")
            self.submit_order(order)
        

    


if __name__ == "__main__":

    if not IS_BACKTESTING:
        strategy = Trend()
        bot = Trader()
        bot.add_strategy(strategy)
        bot.run_all()
    else:
        start = datetime(2023, 1, 1)
        end = datetime(2024, 11, 24)
        Trend.backtest(
            YahooDataBacktesting,
            start,
            end,
            benchmark_asset= "GLD"
        )


# Sample data generation (You would typically load your historical data here)
def generate_sample_data():
    dates = pd.date_range(start='2020-01-01', end='2021-01-01', freq='B')  # Business days
    prices = np.random.normal(loc=100, scale=5, size=len(dates))  # Simulated prices
    return pd.DataFrame(data={'Close': prices}, index=dates)

# Define a simple moving average crossover strategy
class SmaCross(Strategy):
    def init(self):
        # Precompute the moving averages
        self.sma1 = self.I(self.SMA, self.data.Close, 10)  # Short-term SMA
        self.sma2 = self.I(self.SMA, self.data.Close, 30)  # Long-term SMA

    def next(self):
        # Trading logic for crossover
        if self.sma1[-1] > self.sma2[-1] and self.position.is_short:
            self.position.close()  # Close short position
            self.buy()              # Buy signal

        elif self.sma1[-1] < self.sma2[-1] and self.position.is_long:
            self.position.close()  # Close long position
            self.sell()             # Sell signal

# Backtesting function
def run_backtest(data):
    bt = Backtest(data, SmaCross, cash=10_000, commission=.002)
    stats = bt.run()
    print(stats)  # Display backtest statistics
    bt.plot()     # Plot performance

# Main function to check if backtesting is running
def main():
    print("IS_BACKTESTING: True")  # Indicate that backtesting is in progress
    
    # Generate sample data or load your historical data here
    historical_data = generate_sample_data()
    
    # Run the backtest
    run_backtest(historical_data)

if __name__ == "__main__":
    main()
