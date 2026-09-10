"""
Simple API server to expose bot data for dashboard
"""
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__, static_folder='../../frontend/dist')
CORS(app)

STATE_FILE = 'bot/stock_bot_state.json'
LOG_FILE = 'bot/stock_bot_log.json'

@app.route('/api/status')
def get_status():
    """Get current bot status"""
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        
        # Calculate portfolio value
        portfolio_value = state.get('cash', 0)
        positions = state.get('positions', {})
        
        # Add position values (simplified - would need real-time prices)
        for symbol, pos in positions.items():
            portfolio_value += pos['entry_price'] * pos['quantity']
        
        return jsonify({
            'status': 'running',
            'cash': state.get('cash', 0),
            'portfolio_value': portfolio_value,
            'positions_count': len(positions),
            'total_pnl': state.get('total_pnl', 0),
            'wins': state.get('wins', 0),
            'losses': state.get('losses', 0),
            'is_paused': state.get('is_paused', False),
            'started_at': state.get('started_at'),
            'last_updated': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/positions')
def get_positions():
    """Get current positions"""
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        
        positions = []
        for symbol, pos in state.get('positions', {}).items():
            positions.append({
                'symbol': symbol,
                'quantity': pos['quantity'],
                'entry_price': pos['entry_price'],
                'entry_time': pos['entry_time'],
                'confidence': pos.get('confidence', 0),
                'current_price': pos['entry_price'],  # Would need real-time update
                'pnl': 0,  # Would calculate with real-time price
                'pnl_pct': 0
            })
        
        return jsonify(positions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades')
def get_trades():
    """Get trade history"""
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        
        trades = state.get('trades', [])
        # Return last 50 trades
        return jsonify(trades[-50:])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def get_logs():
    """Get recent log entries"""
    try:
        with open(LOG_FILE, 'r') as f:
            logs = json.load(f)
        
        # Return last 100 log entries
        return jsonify(logs[-100:])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve frontend"""
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
