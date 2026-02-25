"""
技术指标计算模块 - 支持常用技术指标
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict, Tuple, List
from dataclasses import dataclass


@dataclass
class IndicatorResult:
    """技术指标结果"""
    name: str  # 指标名称
    values: pd.Series  # 指标值
    signal: Optional[pd.Series] = None  # 信号线 (如MACD的信号线)
    upper_band: Optional[pd.Series] = None  # 上轨 (如布林带)
    lower_band: Optional[pd.Series] = None  # 下轨


class TechnicalIndicators:
    """技术指标计算器"""
    
    @staticmethod
    def sma(prices: pd.Series, period: int = 20) -> pd.Series:
        """
        简单移动平均 (Simple Moving Average)
        
        Args:
            prices: 价格序列
            period: 周期
            
        Returns:
            SMA值序列
        """
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def ema(prices: pd.Series, period: int = 20) -> pd.Series:
        """
        指数移动平均 (Exponential Moving Average)
        
        Args:
            prices: 价格序列
            period: 周期
            
        Returns:
            EMA值序列
        """
        return prices.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def bbands(prices: pd.Series, period: int = 20, 
               std_dev: float = 2.0) -> IndicatorResult:
        """
        布林带 (Bollinger Bands)
        
        Args:
            prices: 价格序列
            period: 周期
            std_dev: 标准差倍数
            
        Returns:
            IndicatorResult with upper_band, signal (中线), lower_band
        """
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        
        return IndicatorResult(
            name="Bollinger Bands",
            values=sma,
            upper_band=upper_band,
            lower_band=lower_band
        )
    
    @staticmethod
    def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        相对强度指数 (Relative Strength Index)
        
        Args:
            prices: 价格序列
            period: 周期
            
        Returns:
            RSI值序列 (0-100)
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def macd(prices: pd.Series, fast: int = 12, slow: int = 26, 
             signal_period: int = 9) -> IndicatorResult:
        """
        MACD (Moving Average Convergence Divergence)
        
        Args:
            prices: 价格序列
            fast: 快速EMA周期
            slow: 慢速EMA周期
            signal_period: 信号线周期
            
        Returns:
            IndicatorResult with MACD, signal, histogram
        """
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        histogram = macd - signal
        
        return IndicatorResult(
            name="MACD",
            values=macd,
            signal=signal,
            upper_band=histogram  # 使用upper_band存储柱状图
        )
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, 
            period: int = 14) -> pd.Series:
        """
        均真波幅 (Average True Range)
        
        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            period: 周期
            
        Returns:
            ATR值序列
        """
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
                   k_period: int = 14, k_smooth: int = 3,
                   d_period: int = 3) -> IndicatorResult:
        """
        随机指标 (Stochastic Oscillator)
        
        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            k_period: K值周期
            k_smooth: K值平滑周期
            d_period: D值周期
            
        Returns:
            IndicatorResult with K线和D线
        """
        low_min = low.rolling(window=k_period).min()
        high_max = high.rolling(window=k_period).max()
        
        k_raw = 100 * (close - low_min) / (high_max - low_min)
        k = k_raw.rolling(window=k_smooth).mean()
        d = k.rolling(window=d_period).mean()
        
        return IndicatorResult(
            name="Stochastic",
            values=k,
            signal=d
        )
    
    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series,
            period: int = 14) -> Dict:
        """
        平均趋向指标 (Average Directional Index)
        
        Returns dict with ADX, +DI, -DI
        """
        tr = pd.concat([
            high - low,
            abs(high - close.shift()),
            abs(low - close.shift())
        ], axis=1).max(axis=1)
        
        atr = tr.rolling(window=period).mean()
        
        # 正向和负向动量
        up = high.diff()
        down = -low.diff()
        
        plus_dm = up.where((up > down) & (up > 0), 0)
        minus_dm = down.where((down > up) & (down > 0), 0)
        
        plus_di = 100 * plus_dm.rolling(window=period).mean() / atr
        minus_di = 100 * minus_dm.rolling(window=period).mean() / atr
        
        di_sum = plus_di + minus_di
        di_diff = abs(plus_di - minus_di)
        
        dx = 100 * di_diff / di_sum
        adx = dx.rolling(window=period).mean()
        
        return {
            'adx': adx,
            'plus_di': plus_di,
            'minus_di': minus_di
        }
    
    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        能量潮 (On-Balance Volume)
        
        Args:
            close: 收盘价序列
            volume: 成交量序列
            
        Returns:
            OBV值序列
        """
        obv = np.where(close > close.shift(), volume, 
                      np.where(close < close.shift(), -volume, 0))
        return pd.Series(obv).cumsum()
    
    @staticmethod
    def vpt(close: pd.Series, high: pd.Series, low: pd.Series,
            volume: pd.Series) -> pd.Series:
        """
        成交量价格趋势 (Volume Price Trend)
        
        Returns:
            VPT值序列
        """
        roc = (close - close.shift()) / close.shift()
        vpt = (roc * volume).fillna(0).cumsum()
        return vpt
    
    @staticmethod
    def pivot_points(high: pd.Series, low: pd.Series, 
                     close: pd.Series) -> Dict[str, pd.Series]:
        """
        支撑阻力位 (Pivot Points)
        
        计算标准支撑/阻力位和中间价
        
        Returns:
            Dict with R2, R1, PP, S1, S2
        """
        pp = (high + low + close) / 3
        
        r1 = (2 * pp) - low
        s1 = (2 * pp) - high
        
        r2 = pp + (high - low)
        s2 = pp - (high - low)
        
        return {
            'R2': r2,
            'R1': r1,
            'PP': pp,
            'S1': s1,
            'S2': s2
        }
    
    @staticmethod
    def calculate_multiple(ohlcv: pd.DataFrame,
                          indicators: List[str]) -> Dict[str, IndicatorResult]:
        """
        批量计算多个技术指标
        
        Args:
            ohlcv: DataFrame包含Open, High, Low, Close, Volume
            indicators: 要计算的指标列表 ['SMA', 'EMA', 'RSI', 'MACD', etc.]
            
        Returns:
            Dict of IndicatorResult
        """
        results = {}
        
        for indicator in indicators:
            if indicator.upper() == 'SMA20':
                results['SMA20'] = IndicatorResult(
                    name='SMA20',
                    values=TechnicalIndicators.sma(ohlcv['Close'], 20)
                )
            elif indicator.upper() == 'SMA50':
                results['SMA50'] = IndicatorResult(
                    name='SMA50',
                    values=TechnicalIndicators.sma(ohlcv['Close'], 50)
                )
            elif indicator.upper() == 'EMA12':
                results['EMA12'] = IndicatorResult(
                    name='EMA12',
                    values=TechnicalIndicators.ema(ohlcv['Close'], 12)
                )
            elif indicator.upper() == 'BBANDS':
                results['BBANDS'] = TechnicalIndicators.bbands(ohlcv['Close'])
            elif indicator.upper() == 'RSI':
                results['RSI'] = IndicatorResult(
                    name='RSI',
                    values=TechnicalIndicators.rsi(ohlcv['Close'])
                )
            elif indicator.upper() == 'MACD':
                results['MACD'] = TechnicalIndicators.macd(ohlcv['Close'])
            elif indicator.upper() == 'ATR':
                results['ATR'] = IndicatorResult(
                    name='ATR',
                    values=TechnicalIndicators.atr(ohlcv['High'], ohlcv['Low'], ohlcv['Close'])
                )
            elif indicator.upper() == 'STOCHASTIC':
                results['STOCHASTIC'] = TechnicalIndicators.stochastic(
                    ohlcv['High'], ohlcv['Low'], ohlcv['Close']
                )
            elif indicator.upper() == 'ADX':
                adx_result = TechnicalIndicators.adx(
                    ohlcv['High'], ohlcv['Low'], ohlcv['Close']
                )
                results['ADX'] = adx_result
            elif indicator.upper() == 'OBV':
                results['OBV'] = IndicatorResult(
                    name='OBV',
                    values=TechnicalIndicators.obv(ohlcv['Close'], ohlcv['Volume'])
                )
            elif indicator.upper() == 'VPT':
                results['VPT'] = IndicatorResult(
                    name='VPT',
                    values=TechnicalIndicators.vpt(ohlcv['Close'], ohlcv['High'],
                                                   ohlcv['Low'], ohlcv['Volume'])
                )
            elif indicator.upper() == 'PIVOT':
                pivot_result = TechnicalIndicators.pivot_points(
                    ohlcv['High'], ohlcv['Low'], ohlcv['Close']
                )
                results['PIVOT'] = pivot_result
        
        return results


class IndicatorAnalyzer:
    """技术指标分析器"""
    
    @staticmethod
    def get_signal(indicator_type: str, values: pd.Series,
                   signal_line: Optional[pd.Series] = None) -> str:
        """
        获取指标信号 ('看涨', '看跌', '中立')
        
        Args:
            indicator_type: 指标类型 ('RSI', 'MACD', etc.)
            values: 指标值
            signal_line: 信号线 (如MACD)
            
        Returns:
            信号字符串
        """
        latest = values.iloc[-1]
        
        if indicator_type == 'RSI':
            if latest < 30:
                return "看涨 (超卖)"
            elif latest > 70:
                return "看跌 (超买)"
            else:
                return "中立"
        
        elif indicator_type == 'MACD':
            if signal_line is not None:
                if values.iloc[-1] > signal_line.iloc[-1] and \
                   values.iloc[-2] <= signal_line.iloc[-2]:
                    return "看涨 (金叉)"
                elif values.iloc[-1] < signal_line.iloc[-1] and \
                     values.iloc[-2] >= signal_line.iloc[-2]:
                    return "看跌 (死叉)"
            return "中立"
        
        elif indicator_type in ['SMA', 'EMA']:
            if values.iloc[-1] > values.iloc[-2]:
                return "看涨"
            elif values.iloc[-1] < values.iloc[-2]:
                return "看跌"
            else:
                return "中立"
        
        else:
            return "中立"
    
    @staticmethod
    def analyze_trend(close: pd.Series, period: int = 20) -> Dict:
        """
        分析趋势
        
        Returns:
            Dict with trend_direction, strength等信息
        """
        sma = close.rolling(window=period).mean()
        ema = close.ewm(span=period, adjust=False).mean()
        
        latest_close = close.iloc[-1]
        latest_sma = sma.iloc[-1]
        latest_ema = ema.iloc[-1]
        
        # 判断趋势
        if latest_close > latest_ema > latest_sma:
            trend = "强势上升"
        elif latest_close > latest_sma:
            trend = "试图上升"
        elif latest_close < latest_ema < latest_sma:
            trend = "强势下降"
        elif latest_close < latest_sma:
            trend = "试图下降"
        else:
            trend = "震荡"
        
        # 计算强度 (基于价格离均线的距离)
        strength = abs(latest_close - latest_sma) / latest_sma * 100
        
        return {
            'trend': trend,
            'strength': strength,
            'latest_close': latest_close,
            'sma': latest_sma,
            'ema': latest_ema
        }
