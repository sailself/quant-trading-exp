# 量化交易平台

## 概述

量化交易平台是一个基于 Python 的应用程序，专为开发、测试和模拟量化交易策略而设计。它旨在提供一个灵活的框架，用于获取市场数据、分析财经新闻，并将传统交易算法与大型语言模型 (LLM) 的洞察力相结合。虽然目前处于开发阶段，LLM 集成和基本 UI 采用模拟组件，但长期愿景包括实时数据处理和实盘交易能力。

## 当前功能

*   **数据采集**:
    *   **股票数据**: 使用 `yfinance` 库获取历史和当前股票价格 (`data/stock_data_fetcher.py`)。
    *   **财经新闻**: 使用 `feedparser` 通过 RSS 源聚合来自各种来源的新闻 (`data/news_events_fetcher.py`)。
    *   **经济事件**: 使用 `icalendar` 库从 iCalendar (.ics) 源解析经济日历 (`data/news_events_fetcher.py`)。
*   **策略实现**:
    *   支持实现各种交易策略。
    *   示例：简单移动平均线 (SMA) 交叉策略 (`strategies/simple_ma_crossover.py`)。
*   **LLM 集成 (模拟)**:
    *   包含一个模拟接口 (`llm_integration/llm_interface.py`)，用于模拟 LLM 驱动的洞察，例如：
        *   基于新闻的市场情绪分析。
        *   未来趋势预测。
        *   最优策略选择。
*   **模拟引擎**:
    *   **`TradingEngine`** (`core_logic/trading_engine.py`): 通过集成数据、LLM 洞察 (模拟) 和策略执行来编排交易决策过程。
    *   **`PortfolioSimulator`** (`simulation/simulator.py`): 跟踪投资组合表现、管理交易 (买入/卖出)、计算盈亏 (P&L) 并维护交易日志。
*   **基本 Web UI**:
    *   一个基于 Flask 的 Web 应用程序 (`ui/app.py`) 提供了一个简单的仪表盘。
    *   目前通过 HTML 模板 (`ui/templates/index.html`) 显示模拟的投资组合数据和策略参数。
*   **模块化设计**:
    *   项目结构清晰，将数据处理、策略逻辑、核心引擎、模拟和 UI 组件分离，以提高可维护性和可扩展性。

## 项目结构

*   `data/`: 用于获取财务数据（股票、新闻、经济事件）的模块。
*   `strategies/`: 各种交易策略的实现。
*   `llm_integration/`: LLM 功能接口（目前为模拟实现）。
*   `core_logic/`: 包含用于决策的核心 `TradingEngine`。
*   `simulation/`: 包含用于回溯测试和性能跟踪的 `PortfolioSimulator`。
*   `ui/`: 用于用户界面的 Flask Web 应用程序。
    *   `ui/templates/`: Web UI 的 HTML 模板。
*   `utils/`: 工具函数和辅助脚本的占位符（目前包含 `.gitkeep`）。
*   `tests/`: 单元测试和集成测试的占位符（目前包含 `.gitkeep`）。
*   `main.py`: 用于配置和运行交易模拟的主脚本。
*   `requirements.txt`: 列出项目的所有 Python 依赖项。
*   `LICENSE`: 项目许可证文件。
*   `README.md`: 本文件（英文版）。

## 设置与安装

1.  **Python 版本**:
    *   推荐使用 Python 3.8+。

2.  **克隆仓库**:
    ```bash
    git clone <repository_url>
    cd quantitative-trading-platform
    ```

3.  **虚拟环境**:
    *   强烈建议使用虚拟环境：
        ```bash
        # 适用于 Linux/macOS
        python3 -m venv venv
        source venv/bin/activate

        # 适用于 Windows
        python -m venv venv
        venv\Scriptsctivate
        ```

4.  **安装依赖**:
    *   使用以下命令安装所有必需的包：
        ```bash
        pip install -r requirements.txt
        ```

## 如何运行

### 后端模拟

1.  **命令**:
    *   运行主交易模拟脚本：
        ```bash
        python main.py
        ```

2.  **预期输出**:
    *   控制台日志详细记录模拟步骤，包括数据获取、策略决策、交易和投资组合更新。
    *   一个名为 `main_run.log` 的日志文件将在项目根目录中创建，其中包含模拟运行的详细日志。
    *   模拟的最终盈亏 (P&L)、执行的交易和投资组合历史摘要将在末尾记录到日志中。

3.  **配置**:
    *   关键模拟参数（如交易代码、模拟持续时间、策略参数等）目前硬编码在 `main.py` 中。修改此文件以更改模拟设置。

### 用户界面

1.  **命令**:
    *   启动 Flask Web UI：
        ```bash
        python ui/app.py
        ```

2.  **访问**:
    *   打开您的网络浏览器并访问 `http://localhost:8080` 或 `http://0.0.0.0:8080`。

3.  **注意**:
    *   UI 当前显示在 `ui/app.py` 中定义的 **模拟数据**。
    *   它 **尚未连接** 到后端模拟引擎或实时数据。 “更新策略和参数” 按钮目前无效。

## 未来开发思路

*   **真实 LLM 集成**: 将模拟 LLM 函数替换为对 LLM API（例如 OpenAI, Hugging Face）的实际调用，以进行情感分析、趋势预测和动态策略调整。
*   **多样化策略**: 实现和测试更多种类的交易策略（例如，基于 RSI 的策略、均值回归策略、基于波动率的策略、配对交易策略）。
*   **UI-后端集成**: 将 Flask UI 连接到后端模拟引擎，以显示真实的模拟结果，允许策略选择并动态可视化性能。
*   **实时数据和经纪商集成**:
    *   与实时数据提供商（例如 WebSockets, 金融 API）集成。
    *   开发用于通过实际经纪账户（例如 Interactive Brokers, Alpaca）执行交易的接口。
*   **高级分析和可视化**: 在 UI 中实现更复杂的图表和性能分析。
*   **数据库集成**: 将交易日志、投资组合历史和市场数据存储在数据库中，以便持久存储和更复杂的查询。
*   **配置管理**: 将硬编码的参数（如 API 密钥、策略设置）移动到配置文件中。
*   **全面测试**: 为所有组件开发强大的单元测试和集成测试套件。
*   **风险管理**: 集成风险管理模块（例如，头寸规模控制、止损订单）。
*   **任务队列**: 用于异步处理长时间运行的进程，如数据获取或 LLM 分析（例如，使用 Celery）。

该平台是构建复杂量化交易系统的一个基础步骤。欢迎贡献和建议。
