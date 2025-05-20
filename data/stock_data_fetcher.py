import yfinance
import pandas as pd
import logging
import os
import re

# Configure basic logging
# Use a specific logger name for this module to avoid conflicts if other modules also use basicConfig
logger = logging.getLogger(__name__)
if not logger.handlers: # Avoid adding multiple handlers if reloaded
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# Ensure the CSV directory exists
CSV_DIR = 'data/csv'
if not os.path.exists(CSV_DIR):
    os.makedirs(CSV_DIR)
    logger.info(f"Created directory: {CSV_DIR}")

def _sanitize_ticker_filename(ticker: str) -> str:
    """Sanitizes a ticker string to be used as a valid filename."""
    return re.sub(r'[^a-zA-Z0-9_-]', '', ticker)

def fetch_historical_data(ticker: str, period: str = '1y', interval: str = '1d', end_date: str | pd.Timestamp = None) -> pd.DataFrame | None:
    """
    Downloads historical market data for a given ticker and saves it to a CSV file.

    Args:
        ticker (str): The ticker symbol to fetch data for (e.g., '^GSPC').
        period (str, optional): The period for which to fetch data (e.g., '1y', '5d', 'max').
                                 Used if end_date is None. Defaults to '1y'.
        interval (str, optional): The interval of data points (e.g., '1d', '1wk', '1mo'). Defaults to '1d'.
        end_date (str | pd.Timestamp, optional): The end date for the historical data.
                                                 If provided, `period` is relative to this `end_date`.
                                                 If None, data is fetched up to the most recent available.
                                                 Defaults to None.

    Returns:
        pd.DataFrame | None: A DataFrame containing the historical data, or None if an error occurs.
    """
    if end_date:
        if isinstance(end_date, str):
            end_date_dt = pd.to_datetime(end_date)
        else:
            end_date_dt = end_date
        # yfinance .history() uses 'end' but calculates start from 'period' relative to 'end'
        # or you can specify 'start' and 'end'.
        # For simplicity with 'period', we'll let yfinance calculate start if end_date is provided.
        # However, yfinance's `period` is typically backwards from the most recent trading day if `end` is today.
        # If `end` is in the past, `period` still goes backward from `end`.
        log_msg = f"Fetching historical data for {ticker} (period: {period}, interval: {interval}, end_date: {end_date_dt.strftime('%Y-%m-%d')})"
        fetch_params = {'period': period, 'interval': interval, 'end': end_date_dt + pd.Timedelta(days=1)}
        # Adding 1 day to end_date because yfinance treats 'end' as exclusive for daily data.
        # To include end_date, we need to specify the day after.
        # For yf.download, the 'end' is exclusive. For Ticker.history, it's inclusive by default for daily data.
        # Let's use yf.download for more explicit start/end control if end_date is specified.

        # Convert period to a start date if end_date is given
        # This logic is simplified; yfinance handles 'period' relative to 'end' well.
        # For more precise control, calculate start_date explicitly if needed.
        # For now, relying on yfinance's handling of period and end.
    else:
        log_msg = f"Fetching historical data for {ticker} (period: {period}, interval: {interval}, end_date: latest)"
        fetch_params = {'period': period, 'interval': interval}

    logger.info(log_msg)
    try:
        stock = yfinance.Ticker(ticker)
        hist_data = stock.history(**fetch_params)
        
        if end_date and not hist_data.empty: # Ensure data does not exceed the requested end_date
             hist_data = hist_data[hist_data.index <= pd.to_datetime(end_date)]


        if hist_data.empty:
            logger.warning(f"No historical data found for {ticker} with parameters: {fetch_params}. It might be an invalid ticker or delisted.")
            return None

        # Clean ticker for filename
        clean_ticker = _sanitize_ticker_filename(ticker)
        date_suffix = f"_{end_date_dt.strftime('%Y%m%d')}" if end_date else "_latest"
        filename = os.path.join(CSV_DIR, f"{clean_ticker}_historical{date_suffix}.csv")
        
        # Only save if significant data is fetched and for main use case, not for every small 'current_price' fetch.
        # This simple check avoids spamming CSV files during simulation's current price fetching.
        if len(hist_data) > 10: # Arbitrary threshold
            hist_data.to_csv(filename)
            logger.info(f"Successfully saved historical data for {ticker} to {filename}")
        else:
            logger.info(f"Historical data for {ticker} fetched but not saved to CSV (too few rows or specific end_date query).")
            
        return hist_data
    except Exception as e:
        logger.error(f"Error fetching historical data for {ticker}: {e}")
        return None

def get_current_price(ticker: str) -> float | None:
    """
    Fetches the most recent closing price for a given ticker.
    For simulation, this might mean fetching data up to 'today' and taking the last close.

    Args:
        ticker (str): The ticker symbol to fetch data for.

    Returns:
        float | None: The current price, or None if an error occurs or price is not available.
    """
    logger.info(f"Fetching current price for {ticker}")
    try:
        # Fetch a short period of data to get the most recent close
        # Using end_date=None to get the most recent data
        data = fetch_historical_data(ticker, period="5d", interval="1d", end_date=None)
        if data is not None and not data.empty:
            current_price_val = data['Close'].iloc[-1]
            logger.info(f"Current price for {ticker}: {current_price_val}")
            return float(current_price_val)
        else:
            # Fallback to Ticker.info if history is empty or fails
            logger.warning(f"Could not get current price for {ticker} via recent history. Trying info object.")
            stock = yfinance.Ticker(ticker)
            info = stock.info
            price = info.get('currentPrice') or \
                    info.get('regularMarketPrice') or \
                    info.get('previousClose')
            
            if price is not None:
                logger.info(f"Current price for {ticker} from info object: {price}")
                return float(price)
            else:
                logger.warning(f"Could not determine current price for {ticker} from info object either.")
                return None
    except Exception as e:
        logger.error(f"Error fetching current price for {ticker}: {e}")
        return None

if __name__ == '__main__':
    # Example Usage (optional - for testing)
    logger.info("Starting stock_data_fetcher example usage...")

    # S&P 500 with end_date
    gspc_data_ended = fetch_historical_data('^GSPC', period='1mo', end_date='2023-12-31')
    if gspc_data_ended is not None:
        logger.info(f"S&P 500 historical data for period ending 2023-12-31 sample:\n{gspc_data_ended.tail()}")

    # S&P 500 latest
    gspc_data_latest = fetch_historical_data('^GSPC', period='1mo')
    if gspc_data_latest is not None:
        logger.info(f"S&P 500 latest historical data sample:\n{gspc_data_latest.head()}")
    
    gspc_price = get_current_price('^GSPC')
    if gspc_price is not None:
        logger.info(f"S&P 500 current price: {gspc_price}")

    # Example of a single stock with end_date
    msft_data_ended = fetch_historical_data('MSFT', period='3mo', end_date='2024-01-15')
    if msft_data_ended is not None:
        logger.info(f"MSFT historical data for period ending 2024-01-15 sample:\n{msft_data_ended.tail()}")

    msft_price = get_current_price('MSFT')
    if msft_price is not None:
        logger.info(f"MSFT current price: {msft_price}")

    # Example of an invalid ticker
    invalid_data = fetch_historical_data('INVALIDTICKERXYZ', period='1mo')
    invalid_price = get_current_price('INVALIDTICKERXYZ')

    logger.info("Stock_data_fetcher example usage finished.")
