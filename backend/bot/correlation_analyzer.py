"""
Correlation Analysis Module
Ensures true diversification by avoiding correlated positions
"""
import numpy as np
from collections import defaultdict

class CorrelationAnalyzer:
    def __init__(self):
        # Predefined correlation groups (stocks that tend to move together)
        self.correlation_groups = {
            'mega_tech': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META'],
            'semiconductors': ['NVDA', 'AMD', 'INTC', 'TSM', 'QCOM', 'MU', 'AVGO'],
            'banks': ['JPM', 'BAC', 'WFC', 'C', 'GS', 'MS'],
            'oil': ['XOM', 'CVX', 'COP', 'SLB', 'EOG'],
            'pharma': ['PFE', 'JNJ', 'MRK', 'ABBV', 'LLY'],
            'retail': ['WMT', 'TGT', 'COST', 'HD', 'LOW'],
            'streaming': ['NFLX', 'DIS', 'PARA'],
            'payments': ['V', 'MA', 'PYPL', 'SQ'],
            'cloud': ['CRM', 'SNOW', 'DDOG', 'NET'],
            'ev': ['TSLA', 'RIVN', 'LCID', 'NIO', 'XPEV'],
            'crypto': ['COIN', 'MSTR', 'RIOT', 'MARA'],
            'chinese_tech': ['BABA', 'JD', 'PDD', 'BIDU'],
            'etfs': ['SPY', 'QQQ', 'IWM', 'DIA', 'VOO', 'VTI']
        }
        
        # Reverse mapping: symbol -> groups
        self.symbol_to_groups = defaultdict(list)
        for group, symbols in self.correlation_groups.items():
            for symbol in symbols:
                self.symbol_to_groups[symbol].append(group)
    
    def get_correlation_groups(self, symbol):
        """Get correlation groups for a symbol"""
        return self.symbol_to_groups.get(symbol, [])
    
    def check_correlation_limit(self, symbol, current_positions, max_per_group=3):
        """Check if adding this symbol would exceed correlation limits"""
        symbol_groups = self.get_correlation_groups(symbol)
        
        if not symbol_groups:
            # Not in any correlation group, OK to add
            return True
        
        # Count how many positions we have in each of this symbol's groups
        for group in symbol_groups:
            group_symbols = self.correlation_groups[group]
            positions_in_group = sum(1 for pos in current_positions if pos in group_symbols)
            
            if positions_in_group >= max_per_group:
                return False
        
        return True
    
    def get_diversification_score(self, current_positions):
        """Calculate how diversified the portfolio is (0-100)"""
        if not current_positions:
            return 100
        
        # Count positions per group
        group_counts = defaultdict(int)
        uncategorized = 0
        
        for symbol in current_positions:
            groups = self.get_correlation_groups(symbol)
            if groups:
                for group in groups:
                    group_counts[group] += 1
            else:
                uncategorized += 1
        
        # Calculate concentration
        total_positions = len(current_positions)
        max_concentration = max(group_counts.values()) if group_counts else 0
        
        # Score: 100 = perfectly diversified, 0 = all in one group
        concentration_penalty = (max_concentration / total_positions) * 50
        diversification_score = 100 - concentration_penalty
        
        return max(0, min(100, diversification_score))
    
    def suggest_diversification(self, current_positions, candidate_symbols):
        """Suggest which symbols would improve diversification"""
        current_groups = set()
        for symbol in current_positions:
            current_groups.update(self.get_correlation_groups(symbol))
        
        # Prioritize symbols from underrepresented groups
        suggestions = []
        for symbol in candidate_symbols:
            if symbol in current_positions:
                continue
            
            symbol_groups = set(self.get_correlation_groups(symbol))
            
            # Calculate overlap with current positions
            overlap = len(symbol_groups & current_groups)
            new_groups = len(symbol_groups - current_groups)
            
            # Score: prefer symbols that add new groups
            diversification_value = new_groups * 2 - overlap
            
            suggestions.append({
                'symbol': symbol,
                'diversification_value': diversification_value,
                'new_groups': new_groups,
                'overlap': overlap
            })
        
        return sorted(suggestions, key=lambda x: x['diversification_value'], reverse=True)
