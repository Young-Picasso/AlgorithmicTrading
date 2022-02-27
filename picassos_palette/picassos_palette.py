# -*- coding: utf-8 -*-
"""

@author: Wilhem Kornhauser
"""

class BaseBacktest:
    """Class for basic event based backtesting of trading strategies.
    
    Attributes
    ==========
    symbol: str
        financial instrument to work with
    start: str
        start date for data selection
    end: str
        end date for data selection
    amount: int, float
        initial investment amount for strategy
    ftc: float
        fixed transaction cost per trade
    ptc: float
        proportional transaction cost per trade
    
    Methods
    =======
    get_data:
        retrieves and prepares data
    plot_data:
        plots the adjusted close values for the financial instrument
    print_balance:
        prints out current account cash balance
    print_net_wealth:
        prints out current account wealth (cash balance + current asset value)
    place_buy_order:
        places market buy order
    place_sell_order:
        places market sell order
    close_out:
        calculates the account net wealth at end of backtesting period. Does not close out open positions in calculation
    """
    
    
    def __init__(self, symbol, start, end, amount, ftc=0.0, ptc=0.0, verbose=True):
        

        if type(symbol) is not str:
            raise ValueError('symbol must be str')
        if type(start) is not str:
            raise ValueError('start must be str')
        if type(end) is not str:
            raise ValueError('end must be str')
        if type(amount) is not (int or float):
            raise ValueError('amount must be int or float')
        if type(ftc) is not float:
            raise ValueError('ftc must be float')
        if type(ptc) is not float:
            raise ValueError('ptc must be float')
               
        self.symbol = symbol # Set financial instrument
        self.start = start # Set start date
        self.end = end # Set end date
        self.initial_amount = amount # Store initial amount in a psuedo-private attribute
        self.amount = amount # Set starting cash balance value
        self.ftc = ftc # Define fixed transaction costs per trade (ie 1 USD per transaction)
        self.ptc = ptc # Defines proportional transaction costs per trade (ie 1% of transaction per transaction)
        self.units = 0 # Units of the instrument (ie number of shares) in the portfolio initially
        self.position = 0 # Sets initial position to market neutral
        self.trade = 0 # Sets initial number of trades to 0
        self.verbose = verbose # Set to True for full output (True by default)
        self.get_data() # Call get_data() method
    
    def __repr__(self):
        return f'BaseBacktest(symbol={self.symbol}, start={self.start}, end={self.end}, amount={self.amount}, ftc={self.ftc}, ptc={self.ptc})'
    
    def get_data(self):
        """
        Retrieves and prepares data
        """
        raw = pd.read_csv('http://hilpisch.com/pyalgo_eikon_eod_data.csv', index_col=0, parse_dates=True).dropna()
        raw = pd.DataFrame(raw[self.symbol])
        raw.loc[self.start:self.end]
        raw.rename(columns={self.symbol: 'price'}, inplace=True)
        raw['return'] = np.log(raw / raw.shift(1))
        self.data = raw.dropna()
        
    def plot_data(self, cols=None):
        """
        Plots the closing prices for financial instrument
        """
        if cols is None:
            cols = ['Price']
        self.data['price'].plot(figsize=(10, 6), title=self.symbol)
        
    def get_date_price(self, bar):
        """
        Returns the date and price for a bar
        """
        date = str(self.data.index[bar])[:10]
        price = self.data.price.iloc[bar]
        return date, price
    
    def print_balance(self, bar):
        """
        Prints out current account cash balance
        """
        date, price = self.get_date_price(bar)
        print(f'{date} | current balance {self.amount:.2f}')
        
    def print_net_wealth(self, bar):
        """
        Prints out current account total wealth (cash balance + positions)
        """
        date, price = self.get_date_price(bar)
        net_wealth = self.units * price + self.amount
        print(f'{date} | current net wealth {net_wealth:.2f}')
        
    def place_buy_order(self, bar, units=None, amount=None):
        """
        Simulates placing a market buy order
        """
        date, price = self.get_date_price(bar)
        if units is None:
            units = int(amount / price) # Note that it is assumed the number of units is always None while the amount is amount of money to be spent buying units.
        self.amount -= (units * price) * (1 + self.ptc) + self.ftc # Note there is no liquidity checking performed.
        self.units+= units
        self.trades += 1
        if self.verbose:
            print(f'{date} | buying {units} units at {price:.2f}')
            self.print_balance(bar)
            self.print_net_wealth(bar)
            
    def place_sell_order(self, bar, units=None, amount=None):
        """
        Simulates placing a market sell order
        """
        date, price = self.get_date_price(bar)
        if units is None:
            units = int(amount / price) # As with place_buy_order, note that units is None and we are selling a set amount of wealth
        self.amount += (units * price) * (1 - self.ptc) - self.ftc
        self.units -= units
        self.trades += 1
        if self.verbose:
            print(f'{date} | selling {units} units at {price:.2f}')
            self.print_balance(bar)
            self.print_net_wealth(bar)
                       
    def close_out(self, bar):
        """
        Calculates accounts net wealth at end of backtest. 
        Does this by summing value of held assets and held cash. 
        Does not account for transaction fees required to close open positions.
        """
        date, price = self.get_date_price(bar)
        self.amount += self.units * price
        self.units = 0
        if self.verbose:
            print(f'{date} | inventory {self.units} units at {price:.2f}')
            print('=' * 55)
            print(f'Final balance [$] {self.amount:.2f}')
            performance  = ((self.amount - self.initial_amount) / self.initial_amount * 100)
            print(f'Net Performance [%] {performance:.2f}')
            print(f'Trades executed [#] {self.trades:.2f}')
            print('=' * 55)
            
    def run_mean_reversion_strategy(self, SMA, threshold):
        """
        Runs a backtest on a mean reversion-based strategy
        
        Parameters
        ==========
        SMA: int
            simple moving average in days
        threshold: float
            absolute value for deviation-based signal relative to SMA
        """
        
        msg = f'\n\nRunning mean reversion strategy | '
        msg += f'SMA={SMA} & threshold={threshold}'
        msg += f'\nfixed costs {self.ftc} | proportional costs {self.ptc}'
        print(msg)
        print('=' * 55)
        
        # Clear data from previous runs
        self.position = 0 
        self.trades = 0
        self.amount = self.initial_amount 
        
        self.data['SMA'] = self.data['price'].rolling(SMA).mean() 
        
        for bar in range(SMA, len(self.data)):
            if self.position == 0: # Checks if market position is neutral
                if (self.data['price'].iloc[bar] < self.data['SMA'].iloc[bar] - threshold): # If market position is neutral, and this gives a buy indicator, buy.
                    self.place_buy_order(bar, amount=self.amount)
                    self.position = 1 # Sets market position to long
            elif self.position == 1: # Checks if market position is long
                if self.data['price'].iloc[bar] >= self.data['SMA'].iloc[bar]: # If market position is long, and this gives a sell signal, sell.
                    self.place_sell_order(bar, units=self.units)
                    self.position = 0 # Set market position to neutral
        self.close_out(bar)