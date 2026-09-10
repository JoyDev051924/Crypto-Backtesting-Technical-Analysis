import { useEffect, useState, useCallback } from 'react';
import './Dashboard.css';

interface BotStatus {
  status: string;
  cash: number;
  portfolio_value: number;
  positions_count: number;
  total_pnl: number;
  wins: number;
  losses: number;
  is_paused: boolean;
  started_at: string;
  last_updated: string;
}

interface Position {
  symbol: string;
  quantity: number;
  entry_price: number;
  entry_time: string;
  confidence: number;
  current_price: number;
  pnl: number;
  pnl_pct: number;
}

interface Trade {
  symbol: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  pnl_pct: number;
  reason: string;
  entry_time: string;
  exit_time: string;
  underlying?: string;
  type?: string;
}

const API_URL = window.location.origin + '/api';

export default function Dashboard() {
  const [status, setStatus] = useState<BotStatus | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [error, setError] = useState<string>('');
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [retryCount, setRetryCount] = useState(0);

  const fetchData = useCallback(async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout

      const [statusRes, positionsRes, tradesRes] = await Promise.all([
        fetch(`${API_URL}/status`, { signal: controller.signal }),
        fetch(`${API_URL}/positions`, { signal: controller.signal }),
        fetch(`${API_URL}/trades`, { signal: controller.signal })
      ]);

      clearTimeout(timeoutId);

      if (statusRes.ok) {
        const statusData = await statusRes.json();
        setStatus(statusData);
        setIsConnected(true);
        setRetryCount(0);
      }
      if (positionsRes.ok) {
        const posData = await positionsRes.json();
        setPositions(posData);
      }
      if (tradesRes.ok) {
        const tradesData = await tradesRes.json();
        setTrades(tradesData);
      }
      
      setError('');
      setLastUpdate(new Date());
    } catch (err: any) {
      console.error('Fetch error:', err);
      setIsConnected(false);
      setRetryCount(prev => prev + 1);
      
      if (err.name === 'AbortError') {
        setError('Connection timeout. Retrying...');
      } else {
        setError(`Connection lost. Retrying... (${retryCount + 1})`);
      }
    }
  }, [retryCount]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, [fetchData]);

  // Calculate time since last update
  const [timeSinceUpdate, setTimeSinceUpdate] = useState(0);
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeSinceUpdate(Math.floor((Date.now() - lastUpdate.getTime()) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [lastUpdate]);

  if (error && !status) {
    return (
      <div className="dashboard">
        <div className="error-container">
          <div className="error-icon">⚠️</div>
          <div className="error-title">Connection Error</div>
          <div className="error-message">{error}</div>
          <div className="error-hint">
            Make sure the bot is running and the API is accessible.
          </div>
          <button onClick={fetchData} className="retry-button">
            Retry Now
          </button>
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="dashboard">
        <div className="loading-container">
          <div className="spinner"></div>
          <div className="loading-text">Connecting to bot...</div>
        </div>
      </div>
    );
  }

  const winRate = status.wins + status.losses > 0 
    ? (status.wins / (status.wins + status.losses) * 100).toFixed(1)
    : '0.0';

  const returnPct = status.portfolio_value > 0
    ? ((status.total_pnl / (status.portfolio_value - status.total_pnl)) * 100).toFixed(2)
    : '0.00';

  const avgWin = status.wins > 0
    ? (trades.filter(t => t.pnl > 0).reduce((sum, t) => sum + t.pnl, 0) / status.wins).toFixed(2)
    : '0.00';

  const avgLoss = status.losses > 0
    ? (trades.filter(t => t.pnl < 0).reduce((sum, t) => sum + t.pnl, 0) / status.losses).toFixed(2)
    : '0.00';

  const profitFactor = status.losses > 0 && parseFloat(avgLoss) !== 0
    ? (Math.abs(parseFloat(avgWin) * status.wins) / Math.abs(parseFloat(avgLoss) * status.losses)).toFixed(2)
    : '0.00';

  const totalInvested = positions.reduce((sum, pos) => sum + (pos.entry_price * pos.quantity), 0);
  const deployedCapital = status.portfolio_value > 0 
    ? ((totalInvested / status.portfolio_value) * 100).toFixed(1)
    : '0.0';

  return (
    <div className="dashboard">
      <header>
        <div className="header-left">
          <h1>🤖 AI Trading Bot</h1>
          <div className="connection-status">
            <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}></span>
            <span className="status-text">
              {isConnected ? 'Connected' : 'Disconnected'}
              {timeSinceUpdate > 0 && ` • ${timeSinceUpdate}s ago`}
            </span>
          </div>
        </div>
        <div className="header-right">
          <div className={`status-badge ${status.is_paused ? 'paused' : 'active'}`}>
            {status.is_paused ? '⚠️ PAUSED' : '✅ ACTIVE'}
          </div>
        </div>
      </header>

      {error && (
        <div className="warning-banner">
          ⚠️ {error}
        </div>
      )}

      <div className="stats-grid">
        <div className="stat-card primary">
          <div className="stat-label">Portfolio Value</div>
          <div className="stat-value">${status.portfolio_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
          <div className="stat-change">
            <span className={returnPct >= '0' ? 'positive' : 'negative'}>
              {returnPct >= '0' ? '▲' : '▼'} {Math.abs(parseFloat(returnPct))}%
            </span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Cash Available</div>
          <div className="stat-value">${status.cash.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
          <div className="stat-subvalue">{deployedCapital}% deployed</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Total P&L</div>
          <div className={`stat-value ${status.total_pnl >= 0 ? 'positive' : 'negative'}`}>
            {status.total_pnl >= 0 ? '+' : ''}${status.total_pnl.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="stat-subvalue">
            {status.wins + status.losses} trades
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Win Rate</div>
          <div className="stat-value">{winRate}%</div>
          <div className="stat-subvalue">
            {status.wins}W / {status.losses}L
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Avg Win</div>
          <div className="stat-value positive">${avgWin}</div>
          <div className="stat-subvalue">per winning trade</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Profit Factor</div>
          <div className={`stat-value ${parseFloat(profitFactor) >= 1 ? 'positive' : 'negative'}`}>
            {profitFactor}x
          </div>
          <div className="stat-subvalue">
            {parseFloat(profitFactor) >= 2 ? 'Excellent' : parseFloat(profitFactor) >= 1.5 ? 'Good' : parseFloat(profitFactor) >= 1 ? 'Profitable' : 'Needs work'}
          </div>
        </div>
      </div>

      <div className="section">
        <div className="section-header">
          <h2>Current Positions ({positions.length})</h2>
          {positions.length > 0 && (
            <div className="section-stats">
              Total Value: ${totalInvested.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          )}
        </div>
        {positions.length === 0 ? (
          <div className="empty">
            <div className="empty-icon">📊</div>
            <div className="empty-text">No open positions</div>
            <div className="empty-hint">Bot is monitoring the market for opportunities</div>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Qty</th>
                  <th>Entry</th>
                  <th>Current</th>
                  <th>P&L</th>
                  <th>Confidence</th>
                  <th>Duration</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((pos, i) => {
                  const duration = Math.floor((Date.now() - new Date(pos.entry_time).getTime()) / 1000 / 60);
                  const hours = Math.floor(duration / 60);
                  const minutes = duration % 60;
                  const durationStr = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
                  
                  return (
                    <tr key={i}>
                      <td className="symbol">{pos.symbol}</td>
                      <td>{pos.quantity}</td>
                      <td>${pos.entry_price.toFixed(2)}</td>
                      <td>${pos.current_price.toFixed(2)}</td>
                      <td className={pos.pnl >= 0 ? 'positive' : 'negative'}>
                        ${pos.pnl.toFixed(2)} ({pos.pnl_pct >= 0 ? '+' : ''}{pos.pnl_pct.toFixed(2)}%)
                      </td>
                      <td>
                        <div className="confidence-bar">
                          <div className="confidence-fill" style={{ width: `${pos.confidence}%` }}></div>
                          <span className="confidence-text">{pos.confidence.toFixed(0)}%</span>
                        </div>
                      </td>
                      <td className="duration">{durationStr}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="section">
        <div className="section-header">
          <h2>Recent Trades</h2>
          {trades.length > 0 && (
            <div className="section-stats">
              Last 20 trades
            </div>
          )}
        </div>
        {trades.length === 0 ? (
          <div className="empty">
            <div className="empty-icon">📈</div>
            <div className="empty-text">No trades yet</div>
            <div className="empty-hint">Trades will appear here once the bot starts trading</div>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Type</th>
                  <th>Entry</th>
                  <th>Exit</th>
                  <th>Qty</th>
                  <th>P&L</th>
                  <th>Reason</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {trades.slice().reverse().slice(0, 20).map((trade, i) => (
                  <tr key={i} className={trade.pnl >= 0 ? 'trade-win' : 'trade-loss'}>
                    <td className="symbol">{trade.underlying || trade.symbol}</td>
                    <td>
                      <span className={`trade-type ${trade.type === 'option' ? 'option' : 'stock'}`}>
                        {trade.type === 'option' ? '📊 Option' : '📈 Stock'}
                      </span>
                    </td>
                    <td>${trade.entry_price.toFixed(2)}</td>
                    <td>${trade.exit_price.toFixed(2)}</td>
                    <td>{trade.quantity}</td>
                    <td className={trade.pnl >= 0 ? 'positive' : 'negative'}>
                      <div className="pnl-cell">
                        <span className="pnl-amount">${trade.pnl.toFixed(2)}</span>
                        <span className="pnl-percent">({trade.pnl_pct >= 0 ? '+' : ''}{trade.pnl_pct.toFixed(2)}%)</span>
                      </div>
                    </td>
                    <td>
                      <span className={`reason-badge ${trade.reason.replace('_', '-')}`}>
                        {trade.reason.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="time">{new Date(trade.exit_time).toLocaleTimeString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <footer>
        <div className="footer-content">
          <div className="footer-left">
            Bot started: {new Date(status.started_at).toLocaleString()}
          </div>
          <div className="footer-right">
            Last updated: {lastUpdate.toLocaleTimeString()} • Auto-refresh: 5s
          </div>
        </div>
      </footer>
    </div>
  );
}
