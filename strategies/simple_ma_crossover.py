import pandas as pd
import numpy as np
import logging
import os
import sys

# Add project root to sys.path to allow imports from data module
# This is a common way to handle imports in a project structure
# For a more robust solution, especially for larger projects, packaging (setup.py) is recommended.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

try:
    from data.stock_data_fetcher import fetch_historical_data
except ImportError:
    # This allows the script to at least define functions if stock_data_fetcher is unavailable
    # The __main__ block will handle the case where fetch_historical_data is None
    fetch_historical_data = None
    logging.warning("Could not import fetch_historical_data. Live data fetching in __main__ will fail.")


# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

def moving_average_crossover_strategy(historical_data: pd.DataFrame, short_window: int = 20, long_window: int = 50) -> pd.DataFrame | None:
    """
    Implements a simple moving average crossover trading strategy.

    Args:
        historical_data (pd.DataFrame): DataFrame with a 'Close' price column and DateTime index.
        short_window (int): The window size for the short-term SMA.
        long_window (int): The window size for the long-term SMA.

    Returns:
        pd.DataFrame | None: A new DataFrame with 'SMA_short', 'SMA_long', and 'Signal' columns,
                             or None if critical checks fail.
    """
    if not isinstance(historical_data, pd.DataFrame):
        logging.error("Input 'historical_data' is not a pandas DataFrame.")
        return None

    if 'Close' not in historical_data.columns:
        logging.error("Required 'Close' column not found in historical_data.")
        return None

    if len(historical_data) < long_window:
        logging.error(f"Historical data length ({len(historical_data)}) is less than the long window ({long_window}). Cannot calculate SMAs.")
        return None
    
    if short_window >= long_window:
        logging.error(f"Short window ({short_window}) must be less than long window ({long_window}).")
        return None

    logging.info(f"Calculating SMAs with short window {short_window} and long window {long_window}.")
    
    # Create a copy to avoid modifying the original DataFrame passed to the function
    data = historical_data.copy()

    data['SMA_short'] = data['Close'].rolling(window=short_window, min_periods=1).mean()
    data['SMA_long'] = data['Close'].rolling(window=long_window, min_periods=1).mean()

    logging.info("Generating trading signals.")
    data['Signal'] = 0 # Hold

    # Buy Signal: SMA_short crosses above SMA_long
    # Condition: SMA_short was below SMA_long in the previous period AND SMA_short is above SMA_long in the current period
    buy_condition = (data['SMA_short'].shift(1) < data['SMA_long'].shift(1)) & \
                    (data['SMA_short'] > data['SMA_long'])
    data.loc[buy_condition, 'Signal'] = 1

    # Sell Signal: SMA_short crosses below SMA_long
    # Condition: SMA_short was above SMA_long in the previous period AND SMA_short is below SMA_long in the current period
    sell_condition = (data['SMA_short'].shift(1) > data['SMA_long'].shift(1)) & \
                     (data['SMA_short'] < data['SMA_long'])
    data.loc[sell_condition, 'Signal'] = -1
    
    # Remove rows with NaN in SMA_long due to insufficient data for the long window,
    # as signals there are not meaningful.
    # Signals are generated based on previous day's SMAs, so the first `long_window -1` rows of SMAs will be NaN.
    # The actual signals start effectively after `long_window` periods.
    # We keep the NaN SMA rows for now, but one might choose to drop them: data.dropna(subset=['SMA_long'], inplace=True)
    
    logging.info("Moving average crossover strategy applied successfully.")
    return data

if __name__ == '__main__':
    logging.info("--- Running Simple Moving Average Crossover Strategy Example ---")
    
    ticker = 'AAPL'
    data_df = None

    if fetch_historical_data:
        logging.info(f"Attempting to fetch historical data for {ticker}...")
        try:
            # Ensure data/csv directory exists if stock_data_fetcher is to save CSVs
            # This check is more for when stock_data_fetcher is run directly, but good practice.
            if not os.path.exists('data/csv'):
                os.makedirs('data/csv')
                logging.info("Created data/csv directory for stock_data_fetcher.")

            data_df = fetch_historical_data(ticker, period='1y')
            if data_df is not None and not data_df.empty:
                logging.info(f"Successfully fetched {len(data_df)} data points for {ticker}.")
            else:
                logging.warning(f"Failed to fetch data for {ticker} or no data returned. Will use mock data.")
                data_df = None # Ensure it's None to trigger mock data
        except Exception as e:
            logging.error(f"Error fetching data for {ticker}: {e}. Will use mock data.")
            data_df = None
    else:
        logging.warning("fetch_historical_data not available. Using mock data.")

    if data_df is None:
        logging.info("Using mock historical data for demonstration.")
        # Create a mock DataFrame
        dates = pd.to_datetime([f'2023-01-{i:02d}' for i in range(1, 31)] + 
                               [f'2023-02-{i:02d}' for i in range(1, 28)] +
                               [f'2023-03-{i:02d}' for i in range(1, 31)] +
                               [f'2023-04-{i:02d}' for i in range(1, 30)])
        # Create a more realistic price series that might actually have crossovers
        np.random.seed(42)
        price_changes = np.random.randn(len(dates)-1) * 0.8
        close_prices = [150]
        for change in price_changes:
            close_prices.append(close_prices[-1] + change)
        
        # Introduce a clearer trend for SMA crossover
        trend = np.linspace(-5, 10, len(dates)) # Down then up
        close_prices = np.array(close_prices) + trend
        close_prices = np.clip(close_prices, 50, 250) # Keep prices in a realistic range

        data_df = pd.DataFrame({'Close': close_prices}, index=dates)
        logging.info(f"Created mock DataFrame with {len(data_df)} data points.")

    if data_df is not None and not data_df.empty:
        logging.info("\nApplying moving average crossover strategy...")
        strategy_df = moving_average_crossover_strategy(data_df, short_window=10, long_window=30) # Using shorter windows for mock data
        
        if strategy_df is not None:
            logging.info(f"\nStrategy DataFrame (tail with {min(15, len(strategy_df))} rows):")
            print(strategy_df[['Close', 'SMA_short', 'SMA_long', 'Signal']].tail(min(15, len(strategy_df))))
            
            # Log a summary of signals
            if 'Signal' in strategy_df.columns:
                buy_signals = strategy_df[strategy_df['Signal'] == 1]
                sell_signals = strategy_df[strategy_df['Signal'] == -1]
                logging.info(f"\nTotal Buy Signals: {len(buy_signals)}")
                logging.info(f"Total Sell Signals: {len(sell_signals)}")
                if not buy_signals.empty:
                    logging.info(f"Last Buy Signal:\n{buy_signals.tail(1)}")
                if not sell_signals.empty:
                    logging.info(f"Last Sell Signal:\n{sell_signals.tail(1)}")
            else:
                logging.warning("Signal column not found in the strategy DataFrame.")
        else:
            logging.error("Failed to apply the strategy.")
    else:
        logging.error("Could not obtain data for the strategy (either fetched or mock).")

    logging.info("\n--- Simple Moving Average Crossover Strategy Example Finished ---")
