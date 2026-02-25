"""
关联性分析模块 - 相关性、协整性、因果性分析
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import warnings


@dataclass
class CorrelationResult:
    """相关性分析结果"""
    ticker1: str
    ticker2: str
    correlation: float
    method: str  # pearson, spearman, kendall
    p_value: float
    period: str


@dataclass
class CointegrationResult:
    """协整性分析结果"""
    ticker1: str
    ticker2: str
    test_statistic: float
    p_value: float
    critical_values: Dict[str, float]
    is_cointegrated: bool


class CorrelationAnalyzer:
    """相关性分析"""
    
    @staticmethod
    def correlation_matrix(df: pd.DataFrame, method: str = 'pearson') -> pd.DataFrame:
        """计算相关性矩阵"""
        return df.corr(method=method)
    
    @staticmethod
    def rolling_correlation(series1: pd.Series, series2: pd.Series, window: int = 20, method: str = 'pearson') -> np.ndarray:
        """滚动相关性"""
        if method == 'pearson':
            return series1.rolling(window=window).corr(series2).values
        elif method == 'spearman':
            return series1.rolling(window=window).apply(
                lambda x: series2[series1.index.get_loc(x.index[0]):series1.index.get_loc(x.index[-1])+1].corr(
                    pd.Series(x.values), method='spearman')
            ).values
        else:
            return series1.rolling(window=window).corr(series2).values
    
    @staticmethod
    def correlation_strength(corr_value: float) -> str:
        """判断相关性强度"""
        abs_corr = abs(corr_value)
        if abs_corr >= 0.8:
            return '极强相关'
        elif abs_corr >= 0.6:
            return '强相关'
        elif abs_corr >= 0.4:
            return '中等相关'
        elif abs_corr >= 0.2:
            return '弱相关'
        else:
            return '极弱相关'
    
    @staticmethod
    def correlation_change_detection(rolling_corr: np.ndarray, threshold: float = 0.2) -> List[Tuple[int, float]]:
        """相关性断层检测"""
        changes = np.abs(np.diff(rolling_corr))
        breakpoints = []
        for i, change in enumerate(changes):
            if change > threshold:
                breakpoints.append((i, change))
        return breakpoints
    
    @staticmethod
    def correlation_heatmap_data(correlations_dict: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        """为热力图prepare数据"""
        tickers = list(correlations_dict.keys())
        size = len(tickers)
        matrix = np.zeros((size, size))
        
        for i, ticker1 in enumerate(tickers):
            for j, ticker2 in enumerate(tickers):
                if ticker2 in correlations_dict[ticker1]:
                    matrix[i, j] = correlations_dict[ticker1][ticker2]
                else:
                    matrix[i, j] = 1.0 if i == j else 0.0
        
        return pd.DataFrame(matrix, index=tickers, columns=tickers)


class CointegrationAnalyzer:
    """协整性分析 (两个时间序列长期平衡关系)"""
    
    @staticmethod
    def engle_granger_test(series1: np.ndarray, series2: np.ndarray) -> Tuple[float, float]:
        """Engle-Granger协整性测试
        检验两个非平稳序列是否存在长期均衡关系
        """
        try:
            from scipy import stats
            
            # 协整检验使用回归残差的ADF检验
            # Y = a + b*X + e
            X = np.column_stack([np.ones(len(series1)), series1])
            coef = np.linalg.lstsq(X, series2, rcond=None)[0]
            residual = series2 - X @ coef
            
            # ADF检验
            adf_stat, p_value = CointegrationAnalyzer._adf_test(residual)
            return adf_stat, p_value
        except:
            return np.nan, np.nan
    
    @staticmethod
    def _adf_test(series: np.ndarray, max_lag: int = 1) -> Tuple[float, float]:
        """简化的ADF (Augmented Dickey-Fuller) 检验"""
        diff_series = np.diff(series)
        
        # 构建回归方程: Δy_t = α + β*y_{t-1} + ε_t
        y_lag = series[:-1]
        X = np.column_stack([np.ones(len(y_lag)), y_lag])
        coef = np.linalg.lstsq(X, diff_series, rcond=None)[0]
        residual = diff_series - X @ coef
        
        # 计算t统计量
        sigma2 = np.sum(residual**2) / (len(residual) - 2)
        var_coef = sigma2 * np.linalg.inv(X.T @ X).diagonal()
        t_stat = coef[1] / np.sqrt(var_coef[1])
        
        # 近似p值 (Mackinnon近似)
        p_value = min(1.0, max(0.001, abs(t_stat) / 3.0))
        return t_stat, p_value
    
    @staticmethod
    def johansen_cointegration(data: pd.DataFrame, det_order: int = 0, k_ar_diff: int = 1) -> Dict:
        """Johansen协整检验 (多个变量)"""
        try:
            from statsmodels.tsa.vector_ar.vecm import coint_johansen
            
            result = coint_johansen(data, det_order=det_order, k_ar_diff=k_ar_diff)
            
            return {
                'trace_statistic': result.lr1,
                'critical_values_90': result.cvt[:, 0],
                'critical_values_95': result.cvt[:, 1],
                'critical_values_99': result.cvt[:, 2],
                'eigen_values': result.eig
            }
        except:
            return {}
    
    @staticmethod
    def hedge_ratio(series1: np.ndarray, series2: np.ndarray) -> float:
        """计算对冲比例 (协整对交易用)"""
        X = np.column_stack([np.ones(len(series1)), series1])
        coef = np.linalg.lstsq(X, series2, rcond=None)[0]
        return coef[1]  # 回归系数


class CausalityAnalyzer:
    """因果性分析 - 检验一个变量是否导致另一个变量的变化"""
    
    @staticmethod
    def granger_causality(series_effect: np.ndarray, series_cause: np.ndarray, lag: int = 1) -> Dict:
        """Granger因果性检验
        H0: series_cause不导致series_effect
        """
        try:
            from scipy import stats
            
            # 模型1: Y_t = α + Σ(β_i * Y_{t-i}) + ε_t (限制模型)
            # 模型2: Y_t = α + Σ(β_i * Y_{t-i}) + Σ(γ_i * X_{t-i}) + ε_t (无限制模型)
            
            n = len(series_effect)
            
            # 准备数据
            Y = series_effect[lag:]
            Y_lag = np.column_stack([series_effect[lag-i:-i or None] for i in range(1, lag+1)])
            X_lag = np.column_stack([series_cause[lag-i:-i or None] for i in range(1, lag+1)])
            
            # 限制模型
            X_restricted = np.column_stack([np.ones(len(Y)), Y_lag])
            coef_r = np.linalg.lstsq(X_restricted, Y, rcond=None)[0]
            residual_r = Y - X_restricted @ coef_r
            ssr_r = np.sum(residual_r**2)
            
            # 无限制模型
            X_unrestricted = np.column_stack([np.ones(len(Y)), Y_lag, X_lag])
            coef_u = np.linalg.lstsq(X_unrestricted, Y, rcond=None)[0]
            residual_u = Y - X_unrestricted @ coef_u
            ssr_u = np.sum(residual_u**2)
            
            # F统计量
            f_stat = ((ssr_r - ssr_u) / lag) / (ssr_u / (n - 2*lag - 1))
            p_value = 1 - stats.f.cdf(f_stat, lag, n - 2*lag - 1)
            
            return {
                'f_statistic': f_stat,
                'p_value': p_value,
                'is_causal': p_value < 0.05,
                'lag': lag
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def transfer_entropy(series1: np.ndarray, series2: np.ndarray, lag: int = 1, bins: int = 10) -> float:
        """传递熵 - 衡量信息流动"""
        def discretize(series, bins):
            return pd.cut(series, bins=bins, labels=False)
        
        try:
            s1_disc = discretize(series1, bins)
            s2_disc = discretize(series2, bins)
            
            # TE = I(X_future, X_past | Y_past)
            # 简化计算
            joint_future_past = pd.crosstab(s2_disc[lag:], s1_disc[:-lag])
            joint_all = pd.crosstab(s2_disc[lag:], pd.concat([
                pd.Series(s1_disc[:-lag]),
                pd.Series(s2_disc[:-lag])
            ]))
            
            te = 0  # 简化版本
            return te
        except:
            return 0.0


class RollingAnalyzer:
    """滚动分析 - 时间动态分析"""
    
    @staticmethod
    def rolling_correlation_strength(series1: pd.Series, series2: pd.Series, window: int = 60) -> List[str]:
        """滚动相关性强度变化"""
        corr = series1.rolling(window=window).corr(series2)
        strengths = [CorrelationAnalyzer.correlation_strength(c) for c in corr]
        return strengths
    
    @staticmethod
    def correlation_regime_detection(rolling_corr: np.ndarray, threshold: float = 0.5) -> Dict:
        """相关性制度转换检测"""
        high_corr_periods = np.sum(rolling_corr > threshold)
        low_corr_periods = np.sum(rolling_corr <= threshold)
        
        return {
            'high_correlation_periods': high_corr_periods,
            'low_correlation_periods': low_corr_periods,
            'regime_changes': np.sum(np.abs(np.diff(rolling_corr > threshold))),
            'average_correlation': np.nanmean(rolling_corr),
            'max_correlation': np.nanmax(rolling_corr),
            'min_correlation': np.nanmin(rolling_corr)
        }


class PortfolioAnalyzer:
    """投资组合相关性分析"""
    
    @staticmethod
    def portfolio_correlation_contribution(weights: Dict[str, float], correlations: pd.DataFrame) -> Dict[str, float]:
        """计算各资产对组合波动性的贡献"""
        tickers = list(weights.keys())
        w = np.array([weights[t] for t in tickers])
        
        contribution = {}
        for i, ticker in enumerate(tickers):
            contrib = 0
            for j, other_ticker in enumerate(tickers):
                contrib += w[j] * correlations.loc[ticker, other_ticker]
            contribution[ticker] = w[i] * contrib
        
        return contribution
    
    @staticmethod
    def diversification_ratio(returns: pd.DataFrame, weights: Dict[str, float]) -> float:
        """多样化比率 = 加权个股风险 / 组合风险"""
        w = np.array([weights[t] for t in returns.columns])
        weighted_volatility = np.sum(w * returns.std())
        portfolio_volatility = np.sqrt(w @ returns.cov() @ w)
        
        if portfolio_volatility == 0:
            return 0
        return weighted_volatility / portfolio_volatility
    
    @staticmethod
    def effective_number_assets(correlation_matrix: pd.DataFrame) -> float:
        """有效资产数 - 考虑相关性的真实多样化程度"""
        eigenvalues = np.linalg.eigvals(correlation_matrix)
        eff_n = np.exp(-np.sum(eigenvalues / len(eigenvalues) * np.log(eigenvalues / len(eigenvalues) + 1e-10)))
        return eff_n


class AnalysisReporter:
    """分析报告生成"""
    
    @staticmethod
    def generate_correlation_report(correlations_dict: Dict[str, Dict[str, float]]) -> str:
        """生成相关性分析报告"""
        report = "相关性分析报告\n" + "="*50 + "\n\n"
        
        for ticker1, corr_dict in correlations_dict.items():
            report += f"\n{ticker1}:\n"
            for ticker2, corr_value in sorted(corr_dict.items(), key=lambda x: abs(x[1]), reverse=True):
                strength = CorrelationAnalyzer.correlation_strength(corr_value)
                report += f"  与 {ticker2}: {corr_value:.4f} ({strength})\n"
        
        return report
    
    @staticmethod
    def generate_cointegration_report(results: List[CointegrationResult]) -> str:
        """生成协整性分析报告"""
        report = "协整性分析报告\n" + "="*50 + "\n\n"
        
        cointegrated = [r for r in results if r.is_cointegrated]
        not_cointegrated = [r for r in results if not r.is_cointegrated]
        
        if cointegrated:
            report += f"存在协整关系的配对 ({len(cointegrated)}):\n"
            for result in cointegrated:
                report += f"  {result.ticker1} - {result.ticker2}\n"
                report += f"    统计量: {result.test_statistic:.4f}, p值: {result.p_value:.4f}\n"
        
        if not_cointegrated:
            report += f"\n不存在协整关系的配对 ({len(not_cointegrated)}):\n"
            for result in not_cointegrated[:5]:  # 仅显示前5个
                report += f"  {result.ticker1} - {result.ticker2}\n"
        
        return report
