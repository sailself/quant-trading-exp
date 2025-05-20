import logging
import pandas as pd
import sys
import os
from datetime import datetime

# Add project root to sys.path to allow imports from other modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Attempt to import LLM interface functions
try:
    from llm_integration import llm_interface
except ImportError:
    logging.critical("CRITICAL: Failed to import llm_interface. TradingEngine cannot operate.")
    # In a real application, this might raise an error or exit.
    # For this structure, we'll let it proceed so the class can be defined,
    # but __init__ will fail if llm_interface is None.
    llm_interface = None

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s')

class TradingEngine:
    def __init__(self, available_strategies: dict):
        """
        Initializes the TradingEngine.

        Args:
            available_strategies (dict): Keys are strategy names (str) and values are strategy functions.
        """
        if llm_interface is None:
            logging.critical("llm_interface not loaded. TradingEngine cannot be initialized.")
            raise ImportError("Failed to load llm_interface module.")

        self.available_strategies = available_strategies
        self.llm_get_market_sentiment = llm_interface.get_market_sentiment
        self.llm_predict_future_trend = llm_interface.predict_future_trend # Though not used in run_trading_cycle as per spec
        self.llm_choose_best_strategy = llm_interface.choose_best_strategy
        logging.info(f"TradingEngine initialized with strategies: {list(available_strategies.keys())}")

    def run_trading_cycle(self, ticker: str, historical_data_provider: callable, 
                          news_provider: callable = None, news_source_params: dict = None) -> dict:
        """
        Runs a single trading cycle for a given ticker.

        Args:
            ticker (str): The stock ticker symbol.
            historical_data_provider (callable): Function to fetch historical data (e.g., fetch_historical_data).
            news_provider (callable, optional): Function to fetch news (e.g., fetch_financial_news_rss).
            news_source_params (dict, optional): Parameters for the news_provider (e.g., {'rss_urls': [...]}).

        Returns:
            dict: A dictionary containing the trading decision and other relevant information.
        """
        logging.info(f"Starting trading cycle for ticker: {ticker}")
        timestamp = pd.Timestamp.now()

        # Default failure dictionary
        failure_dict = {
            'ticker': ticker, 'action': 'ERROR', 'strategy_used': None,
            'latest_signal': None, 'timestamp': timestamp, 'llm_sentiment': None,
            'error_message': 'An unspecified error occurred.'
        }

        # 1. Fetch Data
        logging.info(f"Fetching historical data for {ticker}...")
        try:
            historical_data = historical_data_provider(ticker)
            if historical_data is None or historical_data.empty:
                logging.error(f"No historical data fetched for {ticker}.")
                failure_dict['error_message'] = f"Failed to fetch historical data for {ticker}."
                return failure_dict
            logging.info(f"Successfully fetched {len(historical_data)} historical data points for {ticker}.")
        except Exception as e:
            logging.error(f"Exception fetching historical data for {ticker}: {e}")
            failure_dict['error_message'] = f"Exception fetching historical data: {e}"
            return failure_dict

        news_data = []
        if news_provider:
            logging.info(f"Fetching news for {ticker}...")
            try:
                if news_source_params:
                    news_data = news_provider(**news_source_params)
                else:
                    news_data = news_provider()
                
                if news_data:
                    logging.info(f"Successfully fetched {len(news_data)} news articles.")
                else:
                    logging.info("No news articles fetched or news_provider returned empty.")
            except Exception as e:
                logging.warning(f"Exception fetching news: {e}. Proceeding without news data.")
                news_data = [] # Ensure news_data is an empty list on error

        # 2. Get LLM Insights (Mock)
        news_articles_for_llm = news_data if news_data else []
        logging.info("Getting LLM market sentiment...")
        sentiment = self.llm_get_market_sentiment(news_articles=news_articles_for_llm)
        llm_insights = {'sentiment': sentiment}
        logging.info(f"LLM sentiment: {sentiment}")

        # 3. Select Strategy
        # For simplicity, historical_data summary is just its shape. Could be more complex.
        historical_data_summary_for_llm = {'rows': historical_data.shape[0], 'cols': historical_data.shape[1], 'recent_close': historical_data['Close'].iloc[-5:].tolist() if not historical_data.empty and 'Close' in historical_data else []}
        market_data_for_llm = {'historical_data_summary': historical_data_summary_for_llm}
        
        logging.info("Choosing best strategy via LLM...")
        chosen_strategy_name = self.llm_choose_best_strategy(
            available_strategies=list(self.available_strategies.keys()),
            market_data=market_data_for_llm,
            llm_insights=llm_insights
        )
        logging.info(f"LLM chose strategy: {chosen_strategy_name}")

        if chosen_strategy_name == 'no_strategy_available' or chosen_strategy_name not in self.available_strategies:
            if not self.available_strategies:
                logging.error("No strategies available at all in the engine.")
                failure_dict['error_message'] = "No strategies configured in the engine."
                return failure_dict
            
            old_choice = chosen_strategy_name
            chosen_strategy_name = list(self.available_strategies.keys())[0] # Default to first available
            logging.warning(f"Strategy '{old_choice}' is invalid or unavailable. Defaulting to '{chosen_strategy_name}'.")

        # 4. Execute Strategy
        strategy_function = self.available_strategies.get(chosen_strategy_name)
        if not strategy_function: # Should not happen if defaulting logic above works
            logging.error(f"Strategy function for '{chosen_strategy_name}' not found even after defaulting.")
            failure_dict['error_message'] = f"Strategy function for '{chosen_strategy_name}' not found."
            return failure_dict

        logging.info(f"Executing strategy: {chosen_strategy_name}")
        try:
            # Pass necessary parameters if strategy requires them, e.g., short/long windows for MA crossover
            # For now, assuming strategies take historical_data and have default params or handle None for other params
            data_with_signal = strategy_function(historical_data.copy()) 
            if data_with_signal is None or data_with_signal.empty:
                logging.error(f"Strategy '{chosen_strategy_name}' did not return valid data with signals.")
                failure_dict['error_message'] = f"Strategy '{chosen_strategy_name}' execution failed or returned empty data."
                return failure_dict
            logging.info(f"Strategy '{chosen_strategy_name}' executed successfully.")
        except Exception as e:
            logging.error(f"Exception executing strategy '{chosen_strategy_name}': {e}")
            failure_dict['error_message'] = f"Exception executing strategy '{chosen_strategy_name}': {e}"
            return failure_dict

        # 5. Determine Action
        latest_signal = None
        action = 'HOLD' # Default action
        if 'Signal' in data_with_signal.columns and not data_with_signal.empty:
            try:
                latest_signal_val = data_with_signal['Signal'].iloc[-1]
                if pd.notna(latest_signal_val): # Check if not NaN
                    latest_signal = int(latest_signal_val) # Ensure it's an int for map lookup
                    action_map = {1: 'BUY', -1: 'SELL', 0: 'HOLD'}
                    action = action_map.get(latest_signal, 'HOLD') # Default to HOLD if signal is unexpected
                    logging.info(f"Latest signal: {latest_signal}, Determined action: {action}")
                else:
                    logging.warning("Latest signal is NaN. Defaulting to HOLD.")
                    latest_signal = None # Explicitly set to None if NaN
            except IndexError:
                logging.warning("Could not get latest signal (IndexError - likely empty 'Signal' column after strategy). Defaulting to HOLD.")
            except Exception as e:
                logging.error(f"Error determining action from signal: {e}. Defaulting to HOLD.")
        else:
            logging.warning("'Signal' column not found or DataFrame empty after strategy. Defaulting to HOLD.")

        return {
            'ticker': ticker,
            'action': action,
            'strategy_used': chosen_strategy_name,
            'latest_signal': latest_signal,
            'timestamp': timestamp,
            'llm_sentiment': sentiment,
            'error_message': None # Success
        }

if __name__ == '__main__':
    logging.info("--- Running TradingEngine Main Block Example ---")

    # Adjust sys.path (already done at the top of the file)

    # Import necessary provider and strategy functions
    try:
        from data.stock_data_fetcher import fetch_historical_data
        from data.news_events_fetcher import fetch_financial_news_rss # Using RSS for this example
        from strategies.simple_ma_crossover import moving_average_crossover_strategy
    except ImportError as e:
        logging.critical(f"Failed to import necessary modules for __main__ block: {e}")
        logging.critical("Ensure all modules (data.*, strategies.*) are correctly placed and __init__.py files exist.")
        sys.exit(1) # Exit if core components for the example are missing

    # Define available strategies
    strategies_map = {
        'sma_crossover': moving_average_crossover_strategy
        # Add other strategies here as they are developed
        # 'rsi_momentum': rsi_strategy_function 
    }

    # Instantiate TradingEngine
    try:
        engine = TradingEngine(strategies_map)
    except ImportError: # Handles case where llm_interface failed to load in class definition
        logging.critical("Exiting due to TradingEngine initialization failure (likely llm_interface missing).")
        sys.exit(1)


    # Define parameters for news fetching
    sample_rss_urls = [
        'https://finance.yahoo.com/news/rss',
        'https://www.nasdaq.com/feed/nasdaq-original/rss.xml',
        'http://feeds.marketwatch.com/marketwatch/topstories/'
    ]
    news_params = {'rss_urls': sample_rss_urls, 'max_items_per_feed': 2} # Limit items for example

    # Run trading cycle for a sample ticker
    ticker_symbol = 'MSFT' # Using a common ticker
    logging.info(f"\n--- Running trading cycle for {ticker_symbol} with news ---")
    
    # Ensure data/csv directory exists if stock_data_fetcher is to save CSVs
    # This is more for when stock_data_fetcher runs, but good to ensure for the example.
    csv_dir = os.path.join(PROJECT_ROOT, 'data', 'csv')
    if not os.path.exists(csv_dir):
        try:
            os.makedirs(csv_dir)
            logging.info(f"Created directory: {csv_dir}")
        except OSError as e:
            logging.warning(f"Could not create directory {csv_dir}: {e}. CSV saving might fail.")


    trading_decision = engine.run_trading_cycle(
        ticker_symbol,
        historical_data_provider=fetch_historical_data,
        news_provider=fetch_financial_news_rss,
        news_source_params=news_params
    )
    print(f"\nTrading Decision for {ticker_symbol} (with news):\n{trading_decision}")

    logging.info(f"\n--- Running trading cycle for {ticker_symbol} without news provider ---")
    trading_decision_no_news = engine.run_trading_cycle(
        ticker_symbol,
        historical_data_provider=fetch_historical_data
    )
    print(f"\nTrading Decision for {ticker_symbol} (no news):\n{trading_decision_no_news}")
    
    # Example with a ticker that might fail historical data fetching
    # (assuming "FAKETICKER" is invalid)
    logging.info(f"\n--- Running trading cycle for FAKETICKER (expected to fail data fetching) ---")
    fake_ticker_decision = engine.run_trading_cycle(
        "FAKETICKER",
        historical_data_provider=fetch_historical_data
    )
    print(f"\nTrading Decision for FAKETICKER:\n{fake_ticker_decision}")

    logging.info("\n--- TradingEngine Main Block Example Finished ---")
