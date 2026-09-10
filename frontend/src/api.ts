import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

export interface OHLCV {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface BacktestConfig {
  symbol: string;
  initial_capital: number;
  fee_percent: number;
  strategy: 'sma_crossover' | 'rsi' | 'macd' | 'bollinger_bounce';
  sma_fast: number;
  sma_slow: number;
  rsi_oversold: number;
  rsi_overbought: number;
}

export interface BacktestResult {
  initial_capital: number;
  final_equity: number;
  total_return_pct: number;
  total_trades: number;
  win_rate: number;
  sharpe_ratio: number;
  max_drawdown_pct: number;
  trades: Array<{
    type: 'buy' | 'sell';
    timestamp: string;
    price: number;
    amount: number;
    fee: number;
  }>;
  equity_curve: Array<{
    timestamp: string;
    equity: number;
    price: number;
  }>;
}

export interface Pattern {
  type: string;
  index: number;
  timestamp: string;
  signal: 'bullish' | 'bearish';
  value?: number;
}

export const getSymbols = () => api.get<{ symbols: string[] }>('/market/symbols');

export const getOHLCV = (symbol: string, timeframe: string = '1h', limit: number = 500) =>
  api.get<{ symbol: string; timeframe: string; data: OHLCV[] }>(
    `/market/ohlcv/${symbol.replace('/', '-')}?timeframe=${timeframe}&limit=${limit}`
  );

export const runBacktest = (config: BacktestConfig, data: OHLCV[]) =>
  api.post<BacktestResult>('/backtest/run', { config, data });

export const getIndicators = (data: OHLCV[], indicators: string[]) =>
  api.post<Record<string, number[]>>('/analysis/indicators', { data, indicators });

export const detectPatterns = (data: OHLCV[]) =>
  api.post<{ patterns: Pattern[] }>('/analysis/patterns', { data });

export interface CompareResult {
  strategy: string;
  final_equity: number;
  total_return_pct: number;
  total_trades: number;
  win_rate: number;
  sharpe_ratio: number;
  max_drawdown_pct: number;
}

export const compareStrategies = (data: OHLCV[], initial_capital: number = 10000, fee_percent: number = 0.1) =>
  api.post<{ results: CompareResult[] }>('/backtest/compare', { data, initial_capital, fee_percent });

export const scanMarket = (timeframe: string = '4h') =>
  api.get<{ symbols: Array<{ symbol: string; data: OHLCV[] }> }>(`/market/scan?timeframe=${timeframe}`);

export const runScan = (symbols_data: Array<{ symbol: string; data: OHLCV[] }>, initial_capital: number = 10000, fee_percent: number = 0.1) =>
  api.post<{
    all_results: Array<{
      symbol: string;
      strategy: string;
      return_pct: number;
      buy_hold_pct: number;
      beats_hold: boolean;
      win_rate: number;
      trades: number;
    }>;
    winners: any[];
    total_tested: number;
    total_winners: number;
  }>('/backtest/scan', { symbols_data, initial_capital, fee_percent });
