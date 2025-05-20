# Quantitative Trading Platform

## Overview

The Quantitative Trading Platform is a Python-based application designed for developing, testing, and simulating quantitative trading strategies. It aims to provide a flexible framework for fetching market data, analyzing financial news, and combining traditional trading algorithms with insights from Large Language Models (LLMs). While currently in a developmental stage with mock components for LLM integration and a basic UI, the long-term vision includes real-time data processing and live trading capabilities.

## Documentation in Other Languages

*   **中文 (Chinese)**:
    *   [项目概览 (README_zh.md)](./README_zh.md)
    *   [使用指南 (USAGE_zh.md)](./USAGE_zh.md)

## Current Features

*   **Data Acquisition**:
    *   **Stock Data**: Fetches historical and current stock prices using the `yfinance` library (`data/stock_data_fetcher.py`).
    *   **Financial News**: Aggregates news from various sources via RSS feeds using `feedparser` (`data/news_events_fetcher.py`).
    *   **Economic Events**: Parses economic calendars from iCalendar (.ics) feeds using the `icalendar` library (`data/news_events_fetcher.py`).
*   **Strategy Implementation**:
    *   Supports implementation of various trading strategies.
    *   Example: Simple Moving Average (SMA) Crossover strategy (`strategies/simple_ma_crossover.py`).
*   **LLM Integration (Mock)**:
    *   Includes a mock interface (`llm_integration/llm_interface.py`) for simulating LLM-driven insights, such as:
        *   Market sentiment analysis from news.
        *   Future trend prediction.
        *   Optimal strategy selection.
*   **Simulation Engine**:
    *   **`TradingEngine`** (`core_logic/trading_engine.py`): Orchestrates the trading decision process by integrating data, LLM insights (mocked), and strategy execution.
    *   **`PortfolioSimulator`** (`simulation/simulator.py`): Tracks portfolio performance, manages trades (buys/sells), calculates Profit & Loss (P&L), and maintains a trade log.
*   **Basic Web UI**:
    *   A Flask-based web application (`ui/app.py`) provides a simple dashboard.
    *   Currently displays mock portfolio data and strategy parameters via an HTML template (`ui/templates/index.html`).
*   **Modular Design**:
    *   The project is structured with clearly separated components for data handling, strategy logic, core engine, simulation, and UI, promoting maintainability and scalability.

## Project Structure

*   `data/`: Modules for fetching financial data (stocks, news, economic events).
*   `strategies/`: Implementations of various trading strategies.
*   `llm_integration/`: Interface for LLM functionalities (currently mock implementations).
*   `core_logic/`: Contains the central `TradingEngine` for decision-making.
*   `simulation/`: Includes the `PortfolioSimulator` for backtesting and performance tracking.
*   `ui/`: Flask web application for the user interface.
    *   `ui/templates/`: HTML templates for the web UI.
*   `utils/`: Placeholder for utility functions and helper scripts (currently contains `.gitkeep`).
*   `tests/`: Placeholder for unit and integration tests (currently contains `.gitkeep`).
*   `main.py`: Main script to configure and run trading simulations.
*   `requirements.txt`: Lists all Python dependencies for the project.
*   `LICENSE`: Project license file.
*   `README.md`: This file.

## Setup and Installation

1.  **Python Version**:
    *   Python 3.8+ is recommended.

2.  **Clone the Repository**:
    ```bash
    git clone <repository_url>
    cd quantitative-trading-platform
    ```

3.  **Virtual Environment**:
    *   It is highly recommended to use a virtual environment:
        ```bash
        # For Linux/macOS
        python3 -m venv venv
        source venv/bin/activate

        # For Windows
        python -m venv venv
        venv\Scripts\activate
        ```

4.  **Install Dependencies**:
    *   Install all required packages using:
        ```bash
        pip install -r requirements.txt
        ```

## How to Run

### Backend Simulation

1.  **Command**:
    *   To run the main trading simulation script:
        ```bash
        python main.py
        ```

2.  **Expected Output**:
    *   Console logs detailing the simulation steps, including data fetching, strategy decisions, trades, and portfolio updates.
    *   A log file named `main_run.log` will be created in the root directory with detailed logs of the simulation run.
    *   A summary of the simulation's final Profit & Loss (P&L), executed trades, and portfolio history will be logged at the end.

3.  **Configuration**:
    *   Key simulation parameters such as tickers to trade, simulation duration, and strategy parameters are currently hardcoded within `main.py`. Modify this file to change simulation settings.

### User Interface

1.  **Command**:
    *   To start the Flask web UI:
        ```bash
        python ui/app.py
        ```

2.  **Access**:
    *   Open your web browser and navigate to `http://localhost:8080` or `http://0.0.0.0:8080`.

3.  **Note**:
    *   The UI currently displays **mock data** defined within `ui/app.py`.
    *   It is **not yet connected** to the backend simulation engine or live data. The "Update Strategy & Parameters" button is non-functional.

## Future Development Ideas

*   **Real LLM Integration**: Replace mock LLM functions with actual calls to LLM APIs (e.g., OpenAI, Hugging Face) for sentiment analysis, trend prediction, and dynamic strategy adjustments.
*   **Diverse Strategies**: Implement and test a wider variety of trading strategies (e.g., RSI-based, mean reversion, volatility-based, pairs trading).
*   **UI-Backend Integration**: Connect the Flask UI to the backend simulation engine to display real simulation results, allow strategy selection, and visualize performance dynamically.
*   **Real-Time Data & Brokerage**:
    *   Integrate with real-time data providers (e.g., WebSockets, financial APIs).
    *   Develop an interface for executing trades with actual brokerage accounts (e.g., Interactive Brokers, Alpaca).
*   **Advanced Analytics & Visualization**: Implement more sophisticated charting and performance analytics in the UI.
*   **Database Integration**: Store trade logs, portfolio history, and market data in a database for persistent storage and more complex querying.
*   **Configuration Management**: Move hardcoded parameters (like API keys, strategy settings) to configuration files.
*   **Comprehensive Testing**: Develop a robust suite of unit and integration tests for all components.
*   **Risk Management**: Incorporate risk management modules (e.g., position sizing, stop-loss orders).
*   **Task Queuing**: For handling long-running processes like data fetching or LLM analysis asynchronously (e.g., using Celery).

This platform serves as a foundational step towards building a sophisticated quantitative trading system. Contributions and suggestions are welcome.I have updated the `README.md` file with all the specified sections and content.

The sections included are:
1.  Project Title
2.  Overview
3.  Current Features
4.  Project Structure (accurately mentioning `utils/` and `tests/` as placeholders)
5.  Setup and Installation (including Python version, virtual environment commands, and dependency installation)
6.  How to Run (with separate instructions for backend simulation and UI, including commands and expected outputs/notes)
7.  Future Development Ideas

Markdown formatting (headings, bullet points, code blocks) has been used for clarity and readability.
