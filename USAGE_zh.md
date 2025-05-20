# 项目使用指南

## 引言

本指南旨在帮助用户和开发者理解如何运行模拟、解读其输出，并扩展量化交易平台。内容涵盖配置、输出详情，以及添加新策略、数据源或集成真实 LLM 功能的指导方针。

## 配置模拟 (在 `main.py` 中)

运行交易模拟的主要入口点是位于项目根目录的 `main.py` 脚本。用于配置模拟运行的关键参数可以在此文件中直接找到和修改。

以下是一些您可能想要调整的主要参数：

*   **要模拟的股票代码 (Tickers to Simulate)**: 定义模拟将针对哪些股票代码运行。
    ```python
    tickers_to_simulate = ['AAPL', 'GOOG']
    ```

*   **模拟持续时间 (Simulation Duration)**: 指定模拟将覆盖的（交易）天数，结束于最近的一个工作日。
    ```python
    simulation_days = 5
    ```

*   **策略用的历史数据 (Historical Data for Strategy)**: 定义在每一步决策时，应向交易策略提供多少历史数据。
    ```python
    historical_data_period_for_strategy = '1y' # 例如，1年的数据
    ```

*   **初始投资组合现金 (Initial Portfolio Cash)**: 设置投资组合模拟器的起始现金余额。
    ```python
    portfolio_simulator = PortfolioSimulator(initial_cash=100000.0)
    ```

*   **固定交易数量 (Fixed Trade Quantity)**: 为简单起见，当前模拟以固定数量的股票执行交易。
    ```python
    trade_quantity_fixed = 5
    ```

*   **新闻订阅源 URL (News Feed URLs)**: 指定用于获取财经新闻的 RSS 订阅源 URL。
    ```python
    sample_rss_urls = ["https://finance.yahoo.com/news/rssindex"] 
    # 示例: sample_rss_urls = ["http://feeds.marketwatch.com/marketwatch/realtimeheadlines/"]
    ```

## 解读模拟输出

模拟以下列几种形式提供输出：

*   **控制台日志 (Console Logs)**:
    *   模拟运行时，更新信息会打印到控制台，包括每日处理信息、交易决策以及每个模拟日结束时的投资组合状态。
    *   最终的投资组合表现摘要也会显示出来。

*   **`main_run.log` 文件**:
    *   所有模拟活动的详细、带时间戳的日志都会保存到项目根目录的 `main_run.log` 文件中。每次运行时此文件会被覆盖。
    *   它比控制台输出包含更细致的信息，有助于调试或详细分析。

*   **交易日志 (`portfolio_simulator.trade_log`)**:
    *   这是一个字典列表，每个字典代表一笔已执行的交易。`main.py` 脚本会在模拟结束时记录此日志。
    *   **格式**:
        ```
        {
            'timestamp': pd.Timestamp,  # Time of the trade (交易时间)
            'ticker': str,              # Ticker symbol (股票代码)
            'action': str,              # 'BUY' or 'SELL' (买入或卖出)
            'quantity': int,            # Number of shares (股票数量)
            'price': float,             # Price per share (每股价格)
            'commission': float,        # Commission fee for the trade (交易佣金)
            'cash_after_trade': float   # Cash balance after the trade (交易后现金余额)
        }
        ```

*   **投资组合价值历史 (`portfolio_simulator.portfolio_value_history`)**:
    *   这是一个字典列表，记录了投资组合在不同时间点（通常是每个模拟日结束时和初始时）的状态。`main.py` 脚本会在模拟结束时记录此日志。
    *   **格式**:
        ```
        {
            'timestamp': pd.Timestamp,  # Timestamp of the record (记录时间戳)
            'value': float,             # Total portfolio value (cash + holdings) (总投资组合价值)
            'pnl_percent': float,       # Profit and Loss percentage (盈亏百分比)
            'cash': float,              # Cash balance (现金余额)
            'holdings_value': float     # Market value of all shares held (持股总市值)
        }
        ```
    *   **盈亏计算 (P&L Calculation)**: 盈亏百分比 (`pnl_percent`) 是根据 `PortfolioSimulator` 初始化时提供的 `initial_cash` 的变化计算得出的。

## 使用交易策略

### 位置
交易策略位于 `strategies/` 目录中。

### 示例
提供了一个 `simple_ma_crossover.py` 文件作为策略实现的基本示例。

### 添加新策略

1.  **创建策略文件 (Create Strategy File)**:
    *   在 `strategies/` 目录中创建一个新的 Python 文件（例如，`your_strategy.py`）。

2.  **定义策略函数 (Define Strategy Function)**:
    *   策略的核心将是一个函数。它通常应遵循以下签名：
        ```python
        import pandas as pd

        def my_strategy_function(historical_data: pd.DataFrame, **kwargs) -> pd.DataFrame:
            # historical_data: DataFrame with at least a 'Close' column and DateTimeIndex. (至少包含 'Close' 列和 DateTimeIndex 的 DataFrame)
            # **kwargs: Use for any parameters your strategy needs (e.g., window_short, window_long). (用于策略可能需要的任何参数，例如 window_short, window_long)
            
            data_with_signals = historical_data.copy()
            
            # --- Your strategy logic here --- (你的策略逻辑在此)
            # 1. Calculate indicators (e.g., RSI, MACD, Bollinger Bands). (计算指标)
            #    Store them as new columns in data_with_signals if useful for debugging. (如果对调试有用，将它们作为新列存储在 data_with_signals 中)
            #    Example: data_with_signals['RSI'] = calculate_rsi(data_with_signals['Close'], window=14)

            # 2. Generate the 'Signal' column. This is crucial. (生成 'Signal' 列，这很关键)
            #    - 1: Indicates a BUY signal. (表示买入信号)
            #    - -1: Indicates a SELL signal. (表示卖出信号)
            #    - 0: Indicates a HOLD signal or no action. (表示持有信号或无操作)
            #    Initialize with 0 (Hold). (用0初始化，表示持有)
            data_with_signals['Signal'] = 0
            
            #    Example conditions for signals: (信号条件示例)
            #    buy_condition = (data_with_signals['IndicatorA'] > data_with_signals['IndicatorB'])
            #    sell_condition = (data_with_signals['IndicatorA'] < data_with_signals['IndicatorB'])
            #    data_with_signals.loc[buy_condition, 'Signal'] = 1
            #    data_with_signals.loc[sell_condition, 'Signal'] = -1
            
            return data_with_signals
        ```

3.  **返回值 (Return Value)**:
    *   该函数必须返回一个 pandas DataFrame。
    *   此 DataFrame **必须** 包含原始数据以及一个 `Signal` 列。它还可以包含您计算的任何中间指标列，这对于调试或后续分析可能很有用。

4.  **在 `main.py` 中注册 (Register in `main.py`)**:
    *   要使您的新策略可用于 `TradingEngine`，您需要在 `main.py` 中导入它并将其添加到 `strategies_map` 字典中：
        ```python
        # In main.py (在 main.py 中)
        from strategies.simple_ma_crossover import moving_average_crossover_strategy
        from strategies.your_strategy import my_strategy_function # <-- Import your new function (导入你的新函数)

        # ...

        strategies_map = {
            'sma_crossover': moving_average_crossover_strategy,
            'my_new_strategy_name': my_strategy_function # <-- Add your strategy (添加你的策略)
            # If your strategy function takes parameters, you can use functools.partial or a lambda: (如果你的策略函数接受参数，可以使用 functools.partial 或 lambda)
            # from functools import partial
            # 'my_strategy_with_params': partial(my_strategy_function, param1_value, param2_value)
            # 'my_strategy_lambda_params': lambda df: my_strategy_function(df, param1=x, param2=y)
        }
        ```
    *   `TradingEngine` 使用 `llm_choose_best_strategy`（当前为模拟）函数，该函数从 `strategies_map` 的键中随机选择一个名称。

## 扩展数据获取器 (`data/`)

数据获取模块位于 `data/` 目录中。

*   **`stock_data_fetcher.py`**:
    *   使用 `yfinance` 库获取历史股票数据和当前价格。
    *   可以将获取的历史数据保存到 `data/csv/` 目录下的 CSV 文件中。
    *   支持获取截至特定 `end_date` 的数据。
*   **`news_events_fetcher.py`**:
    *   使用 `feedparser` 从 RSS 源获取财经新闻。
    *   使用 `icalendar` 库从 iCalendar (.ics) 文件解析经济事件。

**添加新数据源的技巧**:
*   识别可靠的 API 或数据源。
*   为这些源使用适当的 Python 客户端/库（例如，通用 API 使用 `requests`，专用 SDK）。
*   为所提供的数据格式（JSON, XML, HTML 等）实现稳健的解析逻辑。
*   包含全面的错误处理（网络问题、API 错误、意外的数据格式）。
*   如果可能，力求输出格式一致，理想情况下，时间序列数据使用 pandas DataFrame，新闻/事件使用字典列表，以简化与平台其余部分的集成。

## LLM 集成 (`llm_integration/llm_interface.py`)

与大型语言模型 (LLM) 的集成由 `llm_integration/` 目录中的模块处理。

*   **当前状态**: **所有 LLM 函数当前均为模拟实现。** 它们返回预定义或随机的输出，并不实际调用任何 LLM API。
*   **接口文件**: `llm_integration/llm_interface.py`
*   **模拟函数**:
    *   `get_market_sentiment(news_articles: list) -> str`:
        *   输入: 新闻文章字典列表。
        *   输出: 模拟的情绪字符串 (例如, 'positive', 'negative', 'neutral')。
    *   `predict_future_trend(historical_data_df: pd.DataFrame = None, news_sentiment: str = None) -> str`:
        *   输入: 可选的历史数据 DataFrame 和新闻情绪字符串。
        *   输出: 模拟的趋势预测 (例如, 'upward', 'downward', 'sideways')。
    *   `choose_best_strategy(available_strategies: list, market_data: dict = None, llm_insights: dict = None) -> str`:
        *   输入: 可用策略名称列表，可选的市场数据和其他 LLM 洞察。
        *   输出: 从提供的列表中随机选择的策略名称。
*   **未来工作**: 此模块的主要目标是将这些模拟函数替换为对 LLM API（例如 OpenAI GPT 系列, Hugging Face 模型）的实际调用。这将涉及处理 API 密钥、提示工程和解析 LLM 响应。

## 用户界面 (`ui/app.py`)

该项目包含一个使用 Flask 构建的基于 Web 的基本用户界面 (UI)。

*   **运行命令**:
    ```bash
    python ui/app.py
    ```
    在您的网络浏览器中通过 `http://localhost:8080` 访问它。

*   **当前状态**:
    *   UI 当前使用在 `ui/app.py` 中定义的 **硬编码模拟数据**。
    *   它 **尚未连接** 到后端模拟引擎 (`TradingEngine`, `PortfolioSimulator`) 或任何实时数据源。

*   **占位符**:
    *   诸如策略选择、参数输入和图表可视化等功能是 HTML 模板 (`ui/templates/index.html`) 中的占位符。
    *   “更新策略和参数” 按钮当前无效。
    *   未来的开发将涉及将这些 UI 元素连接到后端以控制模拟并显示真实结果。

本指南应为使用和开发量化交易平台提供一个坚实的起点。有关更具体的详细信息，请参阅各个模块的文档字符串和注释。
