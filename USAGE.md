# Project Usage Guide

## Introduction

This guide aims to help users and developers understand how to run simulations, interpret their outputs, and extend the Quantitative Trading Platform. It covers configuration, output details, and guidelines for adding new strategies, data sources, or integrating real LLM functionalities.

## Configuring Simulations (in `main.py`)

The primary entry point for running trading simulations is the `main.py` script located in the root of the project. Key parameters for configuring a simulation run can be found and modified directly within this file.

Here are some of the main parameters you might want to adjust:

*   **Tickers to Simulate**: Define which stock tickers the simulation will run for.
    ```python
    tickers_to_simulate = ['AAPL', 'GOOG']
    ```

*   **Simulation Duration**: Specify the number of (trading) days the simulation will cover, ending on the most recent weekday.
    ```python
    simulation_days = 5
    ```

*   **Historical Data for Strategy**: Define how much historical data should be fed into the trading strategy for decision-making at each step.
    ```python
    historical_data_period_for_strategy = '1y' # e.g., 1 year of data
    ```

*   **Initial Portfolio Cash**: Set the starting cash balance for the portfolio simulator.
    ```python
    portfolio_simulator = PortfolioSimulator(initial_cash=100000.0)
    ```

*   **Fixed Trade Quantity**: For simplicity, the current simulation executes trades with a fixed number of shares.
    ```python
    trade_quantity_fixed = 5
    ```

*   **News Feed URLs**: Specify the RSS feed URLs for fetching financial news.
    ```python
    sample_rss_urls = ["https://finance.yahoo.com/news/rssindex"] 
    # Example: sample_rss_urls = ["http://feeds.marketwatch.com/marketwatch/realtimeheadlines/"]
    ```

## Interpreting Simulation Output

The simulation provides output in several forms:

*   **Console Logs**:
    *   As the simulation runs, updates are printed to the console, including daily processing information, trading decisions, and portfolio status at the end of each simulated day.
    *   A final summary of portfolio performance is also displayed.

*   **`main_run.log` File**:
    *   A detailed, timestamped log of all simulation activities is saved to `main_run.log` in the project's root directory. This file is overwritten on each new run.
    *   It contains more granular information than the console output, useful for debugging or detailed analysis.

*   **Trade Log (`portfolio_simulator.trade_log`)**:
    *   This is a list of dictionaries, where each dictionary represents an executed trade. The `main.py` script logs this at the end of the simulation.
    *   **Format**:
        ```
        {
            'timestamp': pd.Timestamp,  # Time of the trade
            'ticker': str,              # Ticker symbol
            'action': str,              # 'BUY' or 'SELL'
            'quantity': int,            # Number of shares
            'price': float,             # Price per share
            'commission': float,        # Commission fee for the trade
            'cash_after_trade': float   # Cash balance after the trade
        }
        ```

*   **Portfolio Value History (`portfolio_simulator.portfolio_value_history`)**:
    *   This is a list of dictionaries, recording the portfolio's state at different points (typically at the end of each simulated day and initially). The `main.py` script logs this at the end.
    *   **Format**:
        ```
        {
            'timestamp': pd.Timestamp,  # Timestamp of the record
            'value': float,             # Total portfolio value (cash + holdings)
            'pnl_percent': float,       # Profit and Loss percentage
            'cash': float,              # Cash balance
            'holdings_value': float     # Market value of all shares held
        }
        ```
    *   **P&L Calculation**: The Profit and Loss percentage (`pnl_percent`) is calculated based on the change from the `initial_cash` provided to the `PortfolioSimulator`.

## Working with Trading Strategies

### Location
Trading strategies are located in the `strategies/` directory.

### Example
A `simple_ma_crossover.py` is provided as a basic example of a strategy implementation.

### Adding a New Strategy

1.  **Create Strategy File**:
    *   Create a new Python file (e.g., `your_strategy.py`) within the `strategies/` directory.

2.  **Define Strategy Function**:
    *   The core of your strategy will be a function. It should generally adhere to the following signature:
        ```python
        import pandas as pd

        def my_strategy_function(historical_data: pd.DataFrame, **kwargs) -> pd.DataFrame:
            # historical_data: DataFrame with at least a 'Close' column and DateTimeIndex.
            # **kwargs: Use for any parameters your strategy needs (e.g., window_short, window_long).
            
            data_with_signals = historical_data.copy()
            
            # --- Your strategy logic here ---
            # 1. Calculate indicators (e.g., RSI, MACD, Bollinger Bands).
            #    Store them as new columns in data_with_signals if useful for debugging.
            #    Example: data_with_signals['RSI'] = calculate_rsi(data_with_signals['Close'], window=14)

            # 2. Generate the 'Signal' column. This is crucial.
            #    - 1: Indicates a BUY signal.
            #    - -1: Indicates a SELL signal.
            #    - 0: Indicates a HOLD signal or no action.
            #    Initialize with 0 (Hold).
            data_with_signals['Signal'] = 0
            
            #    Example conditions for signals:
            #    buy_condition = (data_with_signals['IndicatorA'] > data_with_signals['IndicatorB'])
            #    sell_condition = (data_with_signals['IndicatorA'] < data_with_signals['IndicatorB'])
            #    data_with_signals.loc[buy_condition, 'Signal'] = 1
            #    data_with_signals.loc[sell_condition, 'Signal'] = -1
            
            return data_with_signals
        ```

3.  **Return Value**:
    *   The function must return a pandas DataFrame.
    *   This DataFrame **must** include the original data plus a `Signal` column. It can also include any intermediate indicator columns you calculated, which can be useful for debugging or later analysis.

4.  **Register in `main.py`**:
    *   To make your new strategy available to the `TradingEngine`, you need to import it and add it to the `strategies_map` dictionary in `main.py`:
        ```python
        # In main.py
        from strategies.simple_ma_crossover import moving_average_crossover_strategy
        from strategies.your_strategy import my_strategy_function # <-- Import your new function

        # ...

        strategies_map = {
            'sma_crossover': moving_average_crossover_strategy,
            'my_new_strategy_name': my_strategy_function # <-- Add your strategy
            # If your strategy function takes parameters, you can use functools.partial or a lambda:
            # from functools import partial
            # 'my_strategy_with_params': partial(my_strategy_function, param1_value, param2_value)
            # 'my_strategy_lambda_params': lambda df: my_strategy_function(df, param1=x, param2=y)
        }
        ```
    *   The `TradingEngine` uses the `llm_choose_best_strategy` (currently mock) function, which randomly picks a name from the keys of `strategies_map`.

## Extending Data Fetchers (`data/`)

Data fetching modules are located in the `data/` directory.

*   **`stock_data_fetcher.py`**:
    *   Uses the `yfinance` library to fetch historical stock data and current prices.
    *   Can save fetched historical data to CSV files in `data/csv/`.
    *   Supports fetching data up to a specific `end_date`.
*   **`news_events_fetcher.py`**:
    *   Fetches financial news from RSS feeds using `feedparser`.
    *   Parses economic events from iCalendar (.ics) files using the `icalendar` library.

**Tips for Adding New Data Sources**:
*   Identify reliable APIs or data sources.
*   Use appropriate Python clients/libraries for these sources (e.g., `requests` for general APIs, specialized SDKs).
*   Implement robust parsing logic for the data format provided (JSON, XML, HTML, etc.).
*   Include comprehensive error handling (network issues, API errors, unexpected data format).
*   Aim for a consistent output format if possible, ideally pandas DataFrames for time-series data or lists of dictionaries for news/events, to simplify integration with the rest of the platform.

## LLM Integration (`llm_integration/llm_interface.py`)

The integration with Large Language Models (LLMs) is handled by modules in the `llm_integration/` directory.

*   **Current Status**: **All LLM functions are currently mock implementations.** They return predefined or random outputs and do not make actual calls to any LLM APIs.
*   **Interface File**: `llm_integration/llm_interface.py`
*   **Mock Functions**:
    *   `get_market_sentiment(news_articles: list) -> str`:
        *   Input: A list of news article dictionaries.
        *   Output: A mock sentiment string (e.g., 'positive', 'negative', 'neutral').
    *   `predict_future_trend(historical_data_df: pd.DataFrame = None, news_sentiment: str = None) -> str`:
        *   Input: Optional historical data DataFrame and news sentiment string.
        *   Output: A mock trend prediction (e.g., 'upward', 'downward', 'sideways').
    *   `choose_best_strategy(available_strategies: list, market_data: dict = None, llm_insights: dict = None) -> str`:
        *   Input: List of available strategy names, optional market data, and other LLM insights.
        *   Output: A randomly chosen strategy name from the provided list.
*   **Future Work**: The primary goal for this module is to replace these mock functions with actual calls to LLM APIs (e.g., OpenAI GPT series, Hugging Face models). This would involve handling API keys, prompt engineering, and parsing LLM responses.

## User Interface (`ui/app.py`)

The project includes a basic web-based User Interface (UI) built with Flask.

*   **Run Command**:
    ```bash
    python ui/app.py
    ```
    Access it via `http://localhost:8080` in your web browser.

*   **Current State**:
    *   The UI currently uses **hardcoded mock data** defined within `ui/app.py`.
    *   It is **not connected** to the backend simulation engine (`TradingEngine`, `PortfolioSimulator`) or any live data feeds.

*   **Placeholders**:
    *   Features like strategy selection, parameter inputs, and chart visualizations are placeholders in the HTML template (`ui/templates/index.html`).
    *   The "Update Strategy & Parameters" button is non-functional.
    *   Future development would involve connecting these UI elements to the backend to control simulations and display real results.

This guide should provide a solid starting point for using and developing the Quantitative Trading Platform. Refer to individual module docstrings and comments for more specific details.
