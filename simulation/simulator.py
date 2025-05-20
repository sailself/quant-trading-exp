import logging
import pandas as pd
from datetime import datetime # Used for default timestamp in __main__

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s')

class PortfolioSimulator:
    def __init__(self, initial_cash: float):
        """
        Initializes the PortfolioSimulator.

        Args:
            initial_cash (float): The starting cash for the portfolio.
        """
        self.initial_cash = initial_cash
        self.current_cash = initial_cash
        self.positions = {}  # Stores quantity of each ticker: {'AAPL': 10, 'MSFT': 5}
        self.trade_log = []
        self.portfolio_value_history = []

        # Record initial portfolio value
        initial_timestamp = pd.Timestamp.now()
        self.portfolio_value_history.append({
            'timestamp': initial_timestamp,
            'value': self.initial_cash,
            'pnl_percent': 0.0
        })
        logging.info(f"PortfolioSimulator initialized. Initial cash: ${self.initial_cash:.2f}. Initial portfolio value recorded at {initial_timestamp}.")

    def execute_trade(self, timestamp: pd.Timestamp, ticker: str, action: str, quantity: int, price: float, commission_fee: float = 0.0) -> bool:
        """
        Executes a trade (buy or sell) and updates portfolio state.

        Args:
            timestamp (pd.Timestamp): Time of the trade.
            ticker (str): The stock ticker symbol.
            action (str): 'BUY' or 'SELL'.
            quantity (int): Number of shares to trade.
            price (float): Price per share.
            commission_fee (float, optional): Commission for the trade. Defaults to 0.0.

        Returns:
            bool: True if the trade was successful, False otherwise.
        """
        logging.info(f"Attempting to execute trade: {action} {quantity} {ticker} @ ${price:.2f}, Commission: ${commission_fee:.2f}")

        if action.upper() == 'BUY':
            total_cost = (quantity * price) + commission_fee
            if total_cost > self.current_cash:
                logging.error(f"Trade failed: Insufficient cash for BUY. Cost: ${total_cost:.2f}, Available: ${self.current_cash:.2f}")
                return False
            
            self.current_cash -= total_cost
            self.positions[ticker] = self.positions.get(ticker, 0) + quantity
            trade_type = 'BUY'

        elif action.upper() == 'SELL':
            if self.positions.get(ticker, 0) < quantity:
                logging.error(f"Trade failed: Insufficient shares for SELL. Requested: {quantity}, Available: {self.positions.get(ticker, 0)}")
                return False
            
            total_proceeds = (quantity * price) - commission_fee
            self.current_cash += total_proceeds
            self.positions[ticker] -= quantity
            if self.positions[ticker] == 0:
                del self.positions[ticker]
            trade_type = 'SELL'
        
        else:
            logging.error(f"Trade failed: Invalid action '{action}'. Must be 'BUY' or 'SELL'.")
            return False

        trade_details = {
            'timestamp': timestamp,
            'ticker': ticker,
            'action': trade_type,
            'quantity': quantity,
            'price': price,
            'commission': commission_fee,
            'cash_after_trade': self.current_cash
        }
        self.trade_log.append(trade_details)
        logging.info(f"Trade successful: {trade_details}")
        return True

    def get_current_holdings_value(self, current_market_prices: dict) -> float:
        """
        Calculates the current market value of all holdings.

        Args:
            current_market_prices (dict): {ticker: current_price}.

        Returns:
            float: Total value of all shares currently held.
        """
        holdings_value = 0.0
        for ticker, quantity in self.positions.items():
            price = current_market_prices.get(ticker)
            if price is None:
                logging.warning(f"No current market price found for {ticker} in get_current_holdings_value. Using price 0 for this holding.")
                price = 0.0 # Or handle by fetching last known price if available
            holdings_value += quantity * price
        return holdings_value

    def record_portfolio_value(self, timestamp: pd.Timestamp, current_market_prices: dict):
        """
        Calculates the total portfolio value and records it along with P&L.

        Args:
            timestamp (pd.Timestamp): The timestamp for this portfolio valuation.
            current_market_prices (dict): {ticker: current_price}.
        """
        holdings_value = self.get_current_holdings_value(current_market_prices)
        total_portfolio_value = self.current_cash + holdings_value
        
        if self.initial_cash == 0: # Avoid division by zero if initial cash was 0
            pnl_percent = 0.0 if total_portfolio_value == 0 else float('inf')
        else:
            pnl_percent = ((total_portfolio_value - self.initial_cash) / self.initial_cash) * 100
        
        self.portfolio_value_history.append({
            'timestamp': timestamp,
            'value': total_portfolio_value,
            'pnl_percent': pnl_percent,
            'cash': self.current_cash,
            'holdings_value': holdings_value
        })
        logging.info(f"Portfolio value recorded at {timestamp}: ${total_portfolio_value:.2f} (Cash: ${self.current_cash:.2f}, Holdings: ${holdings_value:.2f}). P&L: {pnl_percent:.2f}%")

    def run_simulation_step(self, trading_decision: dict, current_market_prices: dict, trade_quantity_fixed: int = 10):
        """
        Processes a trading decision, executes a trade if indicated, and records portfolio value.

        Args:
            trading_decision (dict): From TradingEngine (must include 'ticker', 'action', 'timestamp').
            current_market_prices (dict): {ticker: current_price}.
            trade_quantity_fixed (int, optional): Fixed quantity of shares for BUY/SELL trades. Defaults to 10.
        """
        ticker = trading_decision.get('ticker')
        action = trading_decision.get('action')
        timestamp = trading_decision.get('timestamp', pd.Timestamp.now()) # Default to now if not provided

        logging.info(f"Running simulation step for decision: {action} {ticker} at {timestamp}")

        if action and ticker and action.upper() in ['BUY', 'SELL']:
            price = current_market_prices.get(ticker)
            if price is None:
                logging.error(f"No market price available for {ticker} at {timestamp}. Trade cannot be executed.")
            else:
                # For simplicity, using a fixed commission here. Can be made more dynamic.
                commission = 0.01 * trade_quantity_fixed * price # Example: 1% commission
                commission = round(commission, 2) 
                
                self.execute_trade(timestamp, ticker, action, trade_quantity_fixed, price, commission_fee=commission)
        elif action and action.upper() != 'HOLD':
             logging.warning(f"Invalid action '{action}' or missing ticker in trading_decision. No trade executed.")


        # Always record portfolio value for this step, regardless of trade execution
        self.record_portfolio_value(timestamp, current_market_prices)


if __name__ == '__main__':
    logging.info("--- Running PortfolioSimulator Main Block Example ---")

    simulator = PortfolioSimulator(initial_cash=100000)

    # Sample market prices
    market_prices = {
        'AAPL': 150.00,
        'MSFT': 280.00,
        'GOOG': 2200.00
    }

    # Sample trading decisions (simplified structure for direct testing)
    decisions = [
        {'timestamp': pd.Timestamp(datetime(2024, 5, 20, 10, 0, 0)), 'ticker': 'AAPL', 'action': 'BUY'},
        {'timestamp': pd.Timestamp(datetime(2024, 5, 20, 11, 0, 0)), 'ticker': 'MSFT', 'action': 'BUY'},
        # Update market prices
        {'timestamp': pd.Timestamp(datetime(2024, 5, 21, 9, 0, 0)), 'ticker': 'AAPL', 'action': 'HOLD'}, # Hold, price changes
        {'timestamp': pd.Timestamp(datetime(2024, 5, 21, 14, 0, 0)), 'ticker': 'AAPL', 'action': 'SELL'},
        {'timestamp': pd.Timestamp(datetime(2024, 5, 22, 10, 0, 0)), 'ticker': 'GOOG', 'action': 'BUY'},
        {'timestamp': pd.Timestamp(datetime(2024, 5, 22, 11, 0, 0)), 'ticker': 'MSFT', 'action': 'SELL'}, # Sell MSFT
        {'timestamp': pd.Timestamp(datetime(2024, 5, 23, 10, 0, 0)), 'ticker': 'FAKETICKER', 'action': 'BUY'}, # Ticker not in market_prices
        {'timestamp': pd.Timestamp(datetime(2024, 5, 23, 11, 0, 0)), 'ticker': 'AAPL', 'action': 'BUY'}, # Try to buy more AAPL
    ]

    fixed_trade_quantity = 10

    for i, decision in enumerate(decisions):
        # Simulate market price changes for realism
        if decision['timestamp'] > pd.Timestamp(datetime(2024, 5, 20, 12, 0, 0)): # After first trades
            market_prices['AAPL'] = round(market_prices['AAPL'] * (1 + random.uniform(-0.02, 0.03)), 2)
            market_prices['MSFT'] = round(market_prices['MSFT'] * (1 + random.uniform(-0.02, 0.03)), 2)
            market_prices['GOOG'] = round(market_prices['GOOG'] * (1 + random.uniform(-0.02, 0.03)), 2)
            logging.info(f"Market prices updated: {market_prices}")
        
        logging.info(f"\n--- Step {i+1} ---")
        simulator.run_simulation_step(decision, market_prices, trade_quantity_fixed=fixed_trade_quantity)

    print("\n--- Trade Log ---")
    for log_entry in simulator.trade_log:
        print(log_entry)

    print("\n--- Portfolio Value History ---")
    for history_entry in simulator.portfolio_value_history:
        print(f"Timestamp: {history_entry['timestamp']}, Value: ${history_entry['value']:.2f}, P&L: {history_entry['pnl_percent']:.2f}%, Cash: ${history_entry.get('cash', 0):.2f}, Holdings: ${history_entry.get('holdings_value', 0):.2f}")

    final_value = simulator.portfolio_value_history[-1]['value']
    initial_value = simulator.initial_cash
    final_pnl_percent = ((final_value - initial_value) / initial_value) * 100 if initial_value else 0

    print(f"\nInitial Portfolio Value: ${initial_value:.2f}")
    print(f"Final Portfolio Value: ${final_value:.2f}")
    print(f"Final P&L: {final_pnl_percent:.2f}%")
    print(f"Final Cash: ${simulator.current_cash:.2f}")
    print(f"Final Holdings: {simulator.positions}")
    
    logging.info("--- PortfolioSimulator Main Block Example Finished ---")
