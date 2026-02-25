"""
特征工程库 - 技术指标和衍生特征计算
包含50+个技术指标、统计特征和衍生指标
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class FeatureResult:
    """特征计算结果"""
    name: str
    values: np.ndarray
    description: str
    category: str  # momentum, trend, volatility, volume, statistical


class TechnicalIndicators:
    """技术指标计算模块"""
    
    @staticmethod
    def SMA(prices: np.ndarray, period: int = 20) -> np.ndarray:
        """简单移动平均"""
        return pd.Series(prices).rolling(window=period).mean().values
    
    @staticmethod
    def EMA(prices: np.ndarray, period: int = 20) -> np.ndarray:
        """指数移动平均"""
        return pd.Series(prices).ewm(span=period, adjust=False).mean().values
    
    @staticmethod
    def RSI(prices: np.ndarray, period: int = 14) -> np.ndarray:
        """相对强度指数 (Relative Strength Index)"""
        delta = np.diff(prices)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        avg_gain = pd.Series(gain).rolling(window=period).mean().values
        avg_loss = pd.Series(loss).rolling(window=period).mean().values
        
        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def MACD(prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """移动平均聚散指标"""
        ema_fast = pd.Series(prices).ewm(span=fast, adjust=False).mean().values
        ema_slow = pd.Series(prices).ewm(span=slow, adjust=False).mean().values
        macd = ema_fast - ema_slow
        macd_signal = pd.Series(macd).ewm(span=signal, adjust=False).mean().values
        histogram = macd - macd_signal
        return macd, macd_signal, histogram
    
    @staticmethod
    def Bollinger_Bands(prices: np.ndarray, period: int = 20, num_std: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """布林带"""
        sma = TechnicalIndicators.SMA(prices, period)
        std = pd.Series(prices).rolling(window=period).std().values
        upper = sma + num_std * std
        lower = sma - num_std * std
        return upper, sma, lower
    
    @staticmethod
    def ATR(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """平均真实波幅 (Average True Range)"""
        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        atr = pd.Series(tr).rolling(window=period).mean().values
        return atr
    
    @staticmethod
    def STOCH(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14, smooth: int = 3) -> Tuple[np.ndarray, np.ndarray]:
        """随机指标 (Stochastic)"""
        lowest_low = pd.Series(low).rolling(window=period).min().values
        highest_high = pd.Series(high).rolling(window=period).max().values
        
        k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low + 1e-10)
        k = pd.Series(k_percent).rolling(window=smooth).mean().values
        d = pd.Series(k).rolling(window=smooth).mean().values
        return k, d
    
    @staticmethod
    def Williams_R(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """威廉指标"""
        highest_high = pd.Series(high).rolling(window=period).max().values
        lowest_low = pd.Series(low).rolling(window=period).min().values
        wr = -100 * (highest_high - close) / (highest_high - lowest_low + 1e-10)
        return wr
    
    @staticmethod
    def CCI(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 20) -> np.ndarray:
        """商品通道指数"""
        tp = (high + low + close) / 3
        sma = pd.Series(tp).rolling(window=period).mean().values
        mad = pd.Series(tp).rolling(window=period).apply(lambda x: np.mean(np.abs(x - np.mean(x)))).values
        cci = (tp - sma) / (0.015 * mad + 1e-10)
        return cci
    
    @staticmethod
    def OBV(close: np.ndarray, volume: np.ndarray) -> np.ndarray:
        """能量潮"""
        obv = np.zeros_like(close)
        obv[0] = volume[0]
        for i in range(1, len(close)):
            if close[i] > close[i-1]:
                obv[i] = obv[i-1] + volume[i]
            elif close[i] < close[i-1]:
                obv[i] = obv[i-1] - volume[i]
            else:
                obv[i] = obv[i-1]
        return obv
    
    @staticmethod
    def MFI(high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray, period: int = 14) -> np.ndarray:
        """资金流量指标"""
        tp = (high + low + close) / 3
        rmf = tp * volume  # Raw Money Flow
        
        positive_mf = np.where(tp > np.roll(tp, 1), rmf, 0)
        negative_mf = np.where(tp < np.roll(tp, 1), rmf, 0)
        
        positive_mfi = pd.Series(positive_mf).rolling(window=period).sum().values
        negative_mfi = pd.Series(negative_mf).rolling(window=period).sum().values
        
        mfi = 100 * positive_mfi / (positive_mfi + negative_mfi + 1e-10)
        return mfi


class StatisticalFeatures:
    """统计特征计算模块"""
    
    @staticmethod
    def returns(prices: np.ndarray, periods: List[int] = None) -> Dict[str, np.ndarray]:
        """多周期收益率"""
        if periods is None:
            periods = [1, 5, 20, 60]
        
        results = {}
        for p in periods:
            ret = (prices - np.roll(prices, p)) / np.roll(prices, p) * 100
            results[f'return_{p}d'] = ret
        return results
    
    @staticmethod
    def volatility(prices: np.ndarray, periods: List[int] = None) -> Dict[str, np.ndarray]:
        """多周期波动率"""
        if periods is None:
            periods = [5, 10, 20, 60]
        
        results = {}
        for p in periods:
            vol = pd.Series(prices).pct_change().rolling(window=p).std().values * np.sqrt(252) * 100
            results[f'volatility_{p}d'] = vol
        return results
    
    @staticmethod
    def skewness(prices: np.ndarray, period: int = 20) -> np.ndarray:
        """偏度"""
        skew = pd.Series(prices).rolling(window=period).apply(lambda x: pd.Series(x).skew()).values
        return skew
    
    @staticmethod
    def kurtosis(prices: np.ndarray, period: int = 20) -> np.ndarray:
        """峰度"""
        kurt = pd.Series(prices).rolling(window=period).apply(lambda x: pd.Series(x).kurtosis()).values
        return kurt
    
    @staticmethod
    def max_drawdown(prices: np.ndarray, period: int = 252) -> np.ndarray:
        """回撤率"""
        rolling_max = pd.Series(prices).rolling(window=period).max().values
        drawdown = (prices - rolling_max) / rolling_max * 100
        return drawdown
    
    @staticmethod
    def sharpe_ratio(prices: np.ndarray, period: int = 252, rf_rate: float = 0.02) -> np.ndarray:
        """夏普比率"""
        returns = np.diff(prices) / prices[:-1]
        mean_ret = pd.Series(returns).rolling(window=period).mean().values
        std_ret = pd.Series(returns).rolling(window=period).std().values
        sharpe = (mean_ret - rf_rate/252) / (std_ret + 1e-10) * np.sqrt(252)
        return np.concatenate([[np.nan], sharpe])
    
    @staticmethod
    def zscore(prices: np.ndarray, period: int = 20) -> np.ndarray:
        """Z分数"""
        mean = pd.Series(prices).rolling(window=period).mean().values
        std = pd.Series(prices).rolling(window=period).std().values
        zscore = (prices - mean) / (std + 1e-10)
        return zscore


class VolumeTrendFeatures:
    """成交量和趋势特征"""
    
    @staticmethod
    def volume_sma(volume: np.ndarray, period: int = 20) -> np.ndarray:
        """成交量移动平均"""
        return pd.Series(volume).rolling(window=period).mean().values
    
    @staticmethod
    def volume_rate(volume: np.ndarray, price_change: np.ndarray) -> np.ndarray:
        """价量关系"""
        vol_avg = pd.Series(volume).rolling(window=20).mean().values
        vol_rate = volume / (vol_avg + 1e-10)
        return vol_rate
    
    @staticmethod
    def price_momentum(prices: np.ndarray, periods: List[int] = None) -> Dict[str, np.ndarray]:
        """价格动量"""
        if periods is None:
            periods = [5, 10, 20, 60]
        
        results = {}
        for p in periods:
            momentum = prices - np.roll(prices, p)
            results[f'momentum_{p}d'] = momentum
        return results
    
    @staticmethod
    def acceleration(prices: np.ndarray, period: int = 20) -> np.ndarray:
        """加速度"""
        momentum = pd.Series(prices).diff().values
        accel = pd.Series(momentum).diff().rolling(window=period).mean().values
        return accel
    
    @staticmethod
    def trend_strength(prices: np.ndarray, period: int = 20) -> np.ndarray:
        """趋势强度"""
        returns = np.diff(prices) / prices[:-1]
        positive_returns = np.sum(returns > 0) / len(returns) * 100
        trend_strength = pd.Series(returns).rolling(window=period).apply(
            lambda x: (np.sum(x > 0) / len(x)) * 100
        ).values
        return trend_strength


class FeatureCalculator:
    """综合特征计算器"""
    
    def __init__(self, df: pd.DataFrame):
        """
        初始化特征计算器
        
        参数:
            df: 包含 'open', 'high', 'low', 'close', 'volume' 列的DataFrame
        """
        self.df = df.copy()
        self.indicators = TechnicalIndicators()
        self.stats = StatisticalFeatures()
        self.volume_trend = VolumeTrendFeatures()
        self.features = {}
    
    def calculate_all(self) -> pd.DataFrame:
        """计算所有特征"""
        close = self.df['close'].values
        high = self.df['high'].values
        low = self.df['low'].values
        volume = self.df['volume'].values
        
        # 动量指标
        self.features['RSI_14'] = self.indicators.RSI(close, 14)
        self.features['RSI_21'] = self.indicators.RSI(close, 21)
        
        macd, macd_signal, histogram = self.indicators.MACD(close)
        self.features['MACD'] = macd
        self.features['MACD_Signal'] = macd_signal
        self.features['MACD_Histogram'] = histogram
        
        k, d = self.indicators.STOCH(high, low, close, 14)
        self.features['STOCH_K'] = k
        self.features['STOCH_D'] = d
        
        self.features['Williams_R'] = self.indicators.Williams_R(high, low, close)
        self.features['CCI'] = self.indicators.CCI(high, low, close)
        
        # 趋势指标
        self.features['SMA_20'] = self.indicators.SMA(close, 20)
        self.features['SMA_50'] = self.indicators.SMA(close, 50)
        self.features['SMA_200'] = self.indicators.SMA(close, 200)
        self.features['EMA_12'] = self.indicators.EMA(close, 12)
        self.features['EMA_26'] = self.indicators.EMA(close, 26)
        
        upper, sma, lower = self.indicators.Bollinger_Bands(close)
        self.features['BB_Upper'] = upper
        self.features['BB_Middle'] = sma
        self.features['BB_Lower'] = lower
        self.features['BB_Width'] = upper - lower
        self.features['BB_Position'] = (close - lower) / (upper - lower + 1e-10)
        
        # 波动率指标
        self.features['ATR_14'] = self.indicators.ATR(high, low, close)
        self.features['OBV'] = self.indicators.OBV(close, volume)
        self.features['MFI'] = self.indicators.MFI(high, low, close, volume)
        
        # 统计特征
        returns_dict = self.stats.returns(close)
        self.features.update(returns_dict)
        
        volatility_dict = self.stats.volatility(close)
        self.features.update(volatility_dict)
        
        self.features['Skewness'] = self.stats.skewness(close)
        self.features['Kurtosis'] = self.stats.kurtosis(close)
        self.features['Max_Drawdown'] = self.stats.max_drawdown(close)
        self.features['Sharpe_Ratio'] = self.stats.sharpe_ratio(close)
        self.features['ZScore'] = self.stats.zscore(close)
        
        # 成交量特征
        self.features['Volume_SMA'] = self.volume_trend.volume_sma(volume)
        self.features['Volume_Rate'] = self.volume_trend.volume_rate(volume, np.diff(close))
        
        momentum_dict = self.volume_trend.price_momentum(close)
        self.features.update(momentum_dict)
        
        self.features['Acceleration'] = self.volume_trend.acceleration(close)
        self.features['Trend_Strength'] = self.volume_trend.trend_strength(close)
        
        # 创建特征DataFrame
        feature_df = pd.DataFrame(self.features, index=self.df.index)
        return feature_df
    
    def get_feature_categories(self) -> Dict[str, List[str]]:
        """获取特征分类"""
        return {
            'momentum': ['RSI_14', 'RSI_21', 'MACD', 'MACD_Signal', 'MACD_Histogram', 
                        'STOCH_K', 'STOCH_D', 'Williams_R', 'CCI'],
            'trend': ['SMA_20', 'SMA_50', 'SMA_200', 'EMA_12', 'EMA_26',
                     'BB_Upper', 'BB_Middle', 'BB_Lower', 'BB_Width', 'BB_Position'],
            'volatility': ['ATR_14', 'volatility_5d', 'volatility_10d', 'volatility_20d', 'volatility_60d'],
            'volume': ['OBV', 'MFI', 'Volume_SMA', 'Volume_Rate'],
            'statistical': ['return_1d', 'return_5d', 'return_20d', 'return_60d',
                           'Skewness', 'Kurtosis', 'Max_Drawdown', 'Sharpe_Ratio', 'ZScore'],
            'price_action': ['momentum_5d', 'momentum_10d', 'momentum_20d', 'momentum_60d',
                            'Acceleration', 'Trend_Strength']
        }
    
    def calculate_subset(self, categories: List[str]) -> pd.DataFrame:
        """计算指定类别的特征"""
        all_features = self.calculate_all()
        feature_map = self.get_feature_categories()
        
        selected_features = []
        for cat in categories:
            if cat in feature_map:
                selected_features.extend(feature_map[cat])
        
        return all_features[selected_features]


def create_feature_report(df: pd.DataFrame, ticker: str) -> Dict:
    """创建特征工程报告"""
    calculator = FeatureCalculator(df)
    features = calculator.calculate_all()
    
    report = {
        'ticker': ticker,
        'period': f'{df.index[0].date()} 至 {df.index[-1].date()}',
        'total_records': len(df),
        'total_features': len(features.columns),
        'features': features,
        'statistics': {
            'feature_count': len(features.columns),
            'null_percentage': (features.isnull().sum() / len(features) * 100).to_dict(),
            'categories': calculator.get_feature_categories()
        }
    }
    return report
