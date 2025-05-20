from flask import Flask, render_template
from datetime import datetime # For mock data timestamp consistency

app = Flask(__name__)

@app.route('/')
def dashboard():
    """
    Renders the main dashboard page with mock data.
    """
    # Mock data for the dashboard
    portfolio_value = 105250.75
    pnl_percentage = 5.25
    cash = 45250.75
    holdings_value = 60000.00
    
    trade_log = [
        {'timestamp': datetime(2023, 10, 1, 10, 5, 0).strftime('%Y-%m-%d %H:%M:%S'), 'ticker': 'AAPL', 'action': 'BUY', 'quantity': 20, 'price': 175.50, 'cost': 3510.00, 'proceeds': None},
        {'timestamp': datetime(2023, 10, 3, 15, 30, 0).strftime('%Y-%m-%d %H:%M:%S'), 'ticker': 'MSFT', 'action': 'BUY', 'quantity': 10, 'price': 330.20, 'cost': 3302.00, 'proceeds': None},
        {'timestamp': datetime(2023, 10, 5, 11, 15, 0).strftime('%Y-%m-%d %H:%M:%S'), 'ticker': 'AAPL', 'action': 'SELL', 'quantity': 5, 'price': 178.50, 'cost': None, 'proceeds': 892.50}
    ]
    
    available_strategies = ['sma_crossover', 'ema_trending_mock', 'rsi_mean_reversion_mock']
    current_strategy_params = {'name': 'sma_crossover', 'short_window': 20, 'long_window': 50}

    context = {
        'portfolio_value': portfolio_value,
        'pnl_percentage': pnl_percentage,
        'cash': cash,
        'holdings_value': holdings_value,
        'trade_log': trade_log,
        'available_strategies': available_strategies,
        'current_strategy_params': current_strategy_params
    }
    
    return render_template('index.html', **context)

if __name__ == '__main__':
    # Note: For development, using host='0.0.0.0' makes the app accessible externally.
    # In a production environment, a proper WSGI server (like Gunicorn) should be used.
    app.run(debug=True, host='0.0.0.0', port=8080)
