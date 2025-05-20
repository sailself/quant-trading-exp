import logging
import pandas as pd
from datetime import datetime, timedelta # Correct import for timedelta
import os
import sys

# Ensure project root is in sys.path for module imports
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Attempt to import all necessary components
try:
    from data.stock_data_fetcher import fetch_historical_data
    from data.news_events_fetcher import fetch_financial_news_rss # and potentially mock news as a fallback
    # from data.news_events_fetcher import fetch_financial_news_mock # If needed as fallback
    from strategies.simple_ma_crossover import moving_average_crossover_strategy
    from core_logic.trading_engine import TradingEngine
    from simulation.simulator import PortfolioSimulator
except ImportError as e:
    print(f"CRITICAL: Failed to import one or more modules: {e}")
    print("Ensure all modules (data.*, strategies.*, core_logic.*, simulation.*) are correctly placed and __init__.py files exist.")
    sys.exit(1)


# --- Logging Configuration ---
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(funcName)s - %(message)s') # More detailed format

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# File Handler
file_handler = logging.FileHandler('main_run.log', mode='w') # 'w' to overwrite log file on each run
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)

# Specific loggers for modules (optional, if you want finer control or to reduce verbosity from them)
logging.getLogger('yfinance').setLevel(logging.WARNING) # Reduce yfinance verbosity
logging.getLogger('feedparser').setLevel(logging.WARNING) # Reduce feedparser verbosity


def main():
    logging.info("--- Starting Main Trading Simulation Script ---")

    # --- Setup Phase ---
    tickers_to_simulate = ['AAPL', 'GOOG']
    logging.info(f"Tickers to simulate: {tickers_to_simulate}")

    strategies_map = {
        'sma_crossover': moving_average_crossover_strategy
        # Add other strategies here: 'ema_trend': ema_strategy_function
    }
    logging.info(f"Available strategies: {list(strategies_map.keys())}")
    
    try:
        trading_engine = TradingEngine(available_strategies=strategies_map)
    except ImportError as e: # Handles if llm_interface was not loaded in TradingEngine
        logging.critical(f"Failed to initialize TradingEngine: {e}. Exiting.")
        return

    portfolio_simulator = PortfolioSimulator(initial_cash=100000.0)

    # Using a more reliable general news feed. Nasdaq's original feed or specific MarketWatch sections are also good.
    sample_rss_urls = ["https://finance.yahoo.com/news/rssindex"] 
    # Fallback: sample_rss_urls = ["http://feeds.marketwatch.com/marketwatch/realtimeheadlines/"] # This was given
    # sample_rss_urls = ["https://www.nasdaq.com/feed/nasdaq-original/rss.xml"] # Another option from previous tasks
    logging.info(f"News RSS URLs: {sample_rss_urls}")

    simulation_days = 5
    historical_data_period_for_strategy = '1y'
    # For current price, yfinance needs at least 2 days for some intervals to guarantee one point usually.
    # Using '2d' for daily interval to ensure we get the 'end_date's close.
    historical_data_period_for_current_price = '2d' 
    trade_quantity_fixed = 5 # Fixed quantity for trades in this simulation
    
    logging.info(f"Simulation days: {simulation_days}, Strategy data period: {historical_data_period_for_strategy}, Trade quantity: {trade_quantity_fixed}")

    # --- Simulation Loop ---
    # Calculate start date for simulation to end "today" (or most recent weekday if weekend)
    # This makes `current_processing_date` represent a historical date for each loop iteration.
    simulation_end_date = pd.Timestamp.now().normalize()
    if simulation_end_date.dayofweek >= 5: # If today is Sat or Sun
        simulation_end_date = simulation_end_date - pd.Timedelta(days=simulation_end_date.dayofweek - 4) # Go back to Friday

    for day_offset in range(simulation_days -1, -1, -1): # Loop from past to present
        current_processing_date = simulation_end_date - pd.Timedelta(days=day_offset)
        day_number = simulation_days - day_offset
        
        logging.info(f"--- Simulation Day {day_number}/{simulation_days} | Processing Date: {current_processing_date.strftime('%Y-%m-%d')} ---")
        
        all_market_prices_for_step = {}

        # Pre-fetch current prices for all tickers for valuation and trading
        logging.info(f"Fetching current market prices for all tickers for date: {current_processing_date.strftime('%Y-%m-%d')}")
        for ticker_val in tickers_to_simulate:
            try:
                # Fetch data ending on current_processing_date to get its closing price
                # Using a short period like '2d' or '5d' to ensure we get the specific date's close
                df_current_price = fetch_historical_data(
                    ticker=ticker_val, 
                    period=historical_data_period_for_current_price, 
                    interval='1d', # Ensure daily interval
                    end_date=current_processing_date
                )
                if df_current_price is not None and not df_current_price.empty:
                    # Ensure the index is sorted if not already
                    df_current_price = df_current_price.sort_index()
                    # Get the price for the current_processing_date, or the latest available if exact date is missing (e.g. holiday)
                    if current_processing_date in df_current_price.index:
                         current_price = df_current_price.loc[current_processing_date, 'Close']
                    else: # If exact date is not found (e.g. market holiday), take the latest available up to that date.
                         price_series_up_to_date = df_current_price[df_current_price.index <= current_processing_date]
                         if not price_series_up_to_date.empty:
                             current_price = price_series_up_to_date['Close'].iloc[-1]
                         else: # If still no data, this indicates an issue
                             logging.warning(f"No price data found for {ticker_val} at or before {current_processing_date.strftime('%Y-%m-%d')}. Using NaN.")
                             current_price = float('nan') # Or skip ticker
                    
                    if pd.notna(current_price):
                        all_market_prices_for_step[ticker_val] = current_price
                        logging.info(f"Current price for {ticker_val} on {current_processing_date.strftime('%Y-%m-%d')}: {current_price:.2f}")
                    else:
                        logging.warning(f"NaN price for {ticker_val} on {current_processing_date.strftime('%Y-%m-%d')}. Cannot use for trading/valuation.")
                else:
                    logging.warning(f"Could not fetch current price for {ticker_val} for {current_processing_date.strftime('%Y-%m-%d')}.")
            except Exception as e:
                logging.error(f"Exception fetching current price for {ticker_val}: {e}")
        
        if not all_market_prices_for_step:
            logging.error(f"Could not fetch any market prices for {current_processing_date.strftime('%Y-%m-%d')}. Skipping simulation for this day.")
            portfolio_simulator.record_portfolio_value(timestamp=current_processing_date, current_market_prices={}) # Record value with no holdings value change
            continue


        for ticker_to_trade in tickers_to_simulate:
            logging.info(f"Processing ticker for trading: {ticker_to_trade}")

            if ticker_to_trade not in all_market_prices_for_step or pd.isna(all_market_prices_for_step[ticker_to_trade]):
                logging.warning(f"No valid current price for {ticker_to_trade} on {current_processing_date.strftime('%Y-%m-%d')}. Skipping trading for this ticker.")
                continue

            historical_data_for_engine = fetch_historical_data(
                ticker=ticker_to_trade,
                period=historical_data_period_for_strategy,
                interval='1d',
                end_date=current_processing_date # Strategy data should end on the current simulation day
            )

            if historical_data_for_engine is None or historical_data_for_engine.empty:
                logging.warning(f"No historical data for strategy for {ticker_to_trade} ending {current_processing_date.strftime('%Y-%m-%d')}. Skipping ticker.")
                # Record portfolio value even if one ticker fails for strategy data
                # This is done after the loop for all tickers to ensure it's end of day.
                continue 

            logging.info(f"Running trading engine for {ticker_to_trade} with {len(historical_data_for_engine)} data points.")
            
            # Define a lambda that captures the already fetched historical_data_for_engine
            # The trading_engine expects a provider function, but we've pre-fetched the data for this specific end_date
            def current_historical_data_provider(ticker_arg_ignored):
                return historical_data_for_engine

            decision = trading_engine.run_trading_cycle(
                ticker=ticker_to_trade,
                historical_data_provider=current_historical_data_provider,
                news_provider=fetch_financial_news_rss,
                news_source_params={'rss_urls': sample_rss_urls, 'max_items_per_feed': 3}
            )
            
            # Override timestamp with the actual simulation date
            decision['timestamp'] = current_processing_date 
            logging.info(f"Trading decision for {ticker_to_trade}: {decision}")

            if decision['action'] != 'ERROR' and decision['action'] is not None:
                portfolio_simulator.run_simulation_step(
                    trading_decision=decision,
                    current_market_prices=all_market_prices_for_step, # Use the map of current prices
                    trade_quantity_fixed=trade_quantity_fixed
                )
            else:
                logging.warning(f"Trading engine returned an error or no action for {ticker_to_trade}: {decision.get('error_message', 'No action')}. Portfolio value will be recorded without new trades for this ticker.")
                # Portfolio value is recorded once at the end of the day loop for all tickers.
                # If a specific ticker's engine run fails, we don't make a trade for it,
                # but the overall portfolio value is still updated based on current prices.

        # End of day: record portfolio value for all tickers based on the day's closing prices
        portfolio_simulator.record_portfolio_value(timestamp=current_processing_date, current_market_prices=all_market_prices_for_step)
        logging.info(f"End of Day {day_number}: Portfolio Value: ${portfolio_simulator.portfolio_value_history[-1]['value']:.2f}, P&L: {portfolio_simulator.portfolio_value_history[-1]['pnl_percent']:.2f}%")

    # --- Output Results ---
    logging.info("--- Simulation Complete ---")
    if portfolio_simulator.portfolio_value_history:
        logging.info(f"Final Portfolio Value: ${portfolio_simulator.portfolio_value_history[-1]['value']:.2f}")
        logging.info(f"Final P&L: {portfolio_simulator.portfolio_value_history[-1]['pnl_percent']:.2f}%")
    else:
        logging.warning("No portfolio history recorded.")
        
    logging.info(f"Final Cash: ${portfolio_simulator.current_cash:.2f}")
    logging.info(f"Final Holdings: {portfolio_simulator.positions}")

    logging.info("\n--- Trade Log ---")
    if portfolio_simulator.trade_log:
        for trade_idx, trade in enumerate(portfolio_simulator.trade_log):
            logging.info(f"Trade {trade_idx+1}: {trade}")
    else:
        logging.info("No trades were executed.")

    logging.info("\n--- Portfolio History ---")
    if portfolio_simulator.portfolio_value_history:
        for entry_idx, entry in enumerate(portfolio_simulator.portfolio_value_history):
            logging.info(f"Record {entry_idx}: {entry}")
    else:
        logging.info("No portfolio history was recorded (beyond initial).")
    
    logging.info("--- Main Trading Simulation Script Finished ---")

if __name__ == '__main__':
    main()
