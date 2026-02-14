# core/monitor.py
from __future__ import annotations

from datetime import datetime, date, timedelta
from enum import Enum
import pandas as pd
import numpy as np


class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = 4
    WARNING = 3
    INFO = 2
    DEBUG = 1


class AlertType(Enum):
    """Types of alerts"""
    DATA_STALE = "data_stale"
    DATA_MISSING = "data_missing"
    OUTLIER = "outlier"
    EXTREME_MOVE = "extreme_move"
    HIGH_VOLATILITY = "high_volatility"
    CORRELATION_BREAK = "correlation_break"
    STRATEGY_UNDERPERFORMANCE = "strategy_underperformance"
    POSITION_LIMIT = "position_limit"


class Alert:
    """Alert message"""
    
    def __init__(
        self,
        ticker: str,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        timestamp: datetime | None = None,
        metadata: dict | None = None
    ):
        self.ticker = ticker
        self.alert_type = alert_type
        self.severity = severity
        self.message = message
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
    
    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "alert_type": self.alert_type.value,
            "severity": self.severity.name,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class DataMonitor:
    """Monitor data quality"""
    
    def __init__(self, staleness_threshold: int = 2):
        """
        Args:
            staleness_threshold: Days before data is considered stale
        """
        self.staleness_threshold = staleness_threshold
        self.alerts = []
    
    def check_staleness(self, ticker: str, last_date: date) -> Alert | None:
        """Check if data is stale"""
        days_old = (date.today() - last_date).days
        
        if days_old > self.staleness_threshold:
            alert = Alert(
                ticker=ticker,
                alert_type=AlertType.DATA_STALE,
                severity=AlertSeverity.WARNING,
                message=f"Data last updated {days_old} days ago",
                metadata={"days_old": days_old, "last_date": last_date.isoformat()}
            )
            self.alerts.append(alert)
            return alert
        
        return None
    
    def check_missing_values(self, ticker: str, df: pd.DataFrame, threshold: float = 0.05) -> Alert | None:
        """Check for missing values"""
        if df.empty:
            return None
        
        missing_pct = df.isna().sum().sum() / (len(df) * len(df.columns))
        
        if missing_pct > threshold:
            alert = Alert(
                ticker=ticker,
                alert_type=AlertType.DATA_MISSING,
                severity=AlertSeverity.CRITICAL,
                message=f"Data missing {missing_pct*100:.1f}%",
                metadata={"missing_pct": float(missing_pct)}
            )
            self.alerts.append(alert)
            return alert
        
        return None
    
    def check_gaps(self, ticker: str, df: pd.DataFrame, max_gap: int = 5) -> Alert | None:
        """Check for unexpected gaps in data"""
        if df.empty or len(df) < 2:
            return None
        
        dates = pd.to_datetime(df["date"]).sort_values()
        
        gaps = (dates.diff().dt.days).max()
        
        if gaps > max_gap:
            alert = Alert(
                ticker=ticker,
                alert_type=AlertType.DATA_MISSING,
                severity=AlertSeverity.WARNING,
                message=f"Data gap of {gaps} days detected",
                metadata={"max_gap_days": int(gaps)}
            )
            self.alerts.append(alert)
            return alert
        
        return None


class MarketMonitor:
    """Monitor market conditions"""
    
    def __init__(self):
        self.alerts = []
    
    def check_extreme_move(
        self,
        ticker: str,
        current_price: float,
        mean_price: float,
        std_price: float,
        threshold: float = 3.0
    ) -> Alert | None:
        """Check for extreme price moves"""
        if std_price == 0:
            return None
        
        z_score = abs((current_price - mean_price) / std_price)
        
        if z_score > threshold:
            alert = Alert(
                ticker=ticker,
                alert_type=AlertType.EXTREME_MOVE,
                severity=AlertSeverity.WARNING,
                message=f"Extreme price move: {z_score:.1f} std deviations",
                metadata={"z_score": float(z_score), "current_price": float(current_price)}
            )
            self.alerts.append(alert)
            return alert
        
        return None
    
    def check_high_volatility(
        self,
        ticker: str,
        volatility: float,
        hist_mean_vol: float,
        threshold: float = 2.0
    ) -> Alert | None:
        """Check for abnormally high volatility"""
        if volatility > hist_mean_vol * threshold:
            alert = Alert(
                ticker=ticker,
                alert_type=AlertType.HIGH_VOLATILITY,
                severity=AlertSeverity.WARNING,
                message=f"High volatility: {volatility:.2f} (normal: {hist_mean_vol:.2f})",
                metadata={"volatility": float(volatility), "normal_vol": float(hist_mean_vol)}
            )
            self.alerts.append(alert)
            return alert
        
        return None
    
    def check_correlation_break(
        self,
        ticker1: str,
        ticker2: str,
        current_corr: float,
        hist_mean_corr: float,
        threshold: float = 2.0
    ) -> Alert | None:
        """Check for correlation breakdown"""
        corr_change = abs(current_corr - hist_mean_corr)
        
        if corr_change > threshold:
            alert = Alert(
                ticker=ticker1,
                alert_type=AlertType.CORRELATION_BREAK,
                severity=AlertSeverity.WARNING,
                message=f"Correlation with {ticker2} broken: {current_corr:.2f} (historical: {hist_mean_corr:.2f})",
                metadata={
                    "pair": f"{ticker1}-{ticker2}",
                    "current_corr": float(current_corr),
                    "hist_mean_corr": float(hist_mean_corr)
                }
            )
            self.alerts.append(alert)
            return alert
        
        return None


class StrategyMonitor:
    """Monitor strategy performance"""
    
    def __init__(self):
        self.alerts = []
    
    def check_underperformance(
        self,
        strategy_name: str,
        current_return: float,
        hist_mean_return: float,
        threshold: float = 0.5  # -50% relative performance
    ) -> Alert | None:
        """Check for strategy underperformance"""
        if hist_mean_return == 0:
            return None
        
        relative_performance = (current_return - hist_mean_return) / abs(hist_mean_return)
        
        if relative_performance < threshold:
            alert = Alert(
                ticker=strategy_name,
                alert_type=AlertType.STRATEGY_UNDERPERFORMANCE,
                severity=AlertSeverity.WARNING,
                message=f"Strategy underperforming: {current_return:.2f}% vs {hist_mean_return:.2f}% historical",
                metadata={
                    "strategy": strategy_name,
                    "current_return": float(current_return),
                    "hist_return": float(hist_mean_return),
                    "relative_perf": float(relative_performance)
                }
            )
            self.alerts.append(alert)
            return alert
        
        return None
    
    def check_drawdown(
        self,
        strategy_name: str,
        current_drawdown: float,
        max_drawdown_limit: float = -0.20  # -20%
    ) -> Alert | None:
        """Check for excessive drawdown"""
        if current_drawdown < max_drawdown_limit:
            alert = Alert(
                ticker=strategy_name,
                alert_type=AlertType.STRATEGY_UNDERPERFORMANCE,
                severity=AlertSeverity.CRITICAL,
                message=f"Drawdown limit exceeded: {current_drawdown*100:.1f}%",
                metadata={
                    "strategy": strategy_name,
                    "drawdown": float(current_drawdown),
                    "limit": float(max_drawdown_limit)
                }
            )
            self.alerts.append(alert)
            return alert
        
        return None


class AlertAggregator:
    """Aggregate and manage alerts"""
    
    def __init__(self):
        self.alerts: list[Alert] = []
    
    def add_alert(self, alert: Alert) -> None:
        """Add an alert"""
        self.alerts.append(alert)
    
    def get_alerts(self, severity: AlertSeverity | None = None) -> list[dict]:
        """Get alerts, optionally filtered by severity"""
        alerts = self.alerts
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return [a.to_dict() for a in sorted(alerts, key=lambda x: x.timestamp, reverse=True)]
    
    def get_summary(self) -> dict:
        """Get alert summary"""
        by_severity = {}
        for alert in self.alerts:
            key = alert.severity.name
            by_severity[key] = by_severity.get(key, 0) + 1
        
        by_type = {}
        for alert in self.alerts:
            key = alert.alert_type.value
            by_type[key] = by_type.get(key, 0) + 1
        
        return {
            "total_alerts": len(self.alerts),
            "by_severity": by_severity,
            "by_type": by_type,
            "critical_count": len([a for a in self.alerts if a.severity == AlertSeverity.CRITICAL])
        }
    
    def clear(self) -> None:
        """Clear alerts"""
        self.alerts = []
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert alerts to DataFrame"""
        if not self.alerts:
            return pd.DataFrame()
        
        return pd.DataFrame([a.to_dict() for a in self.alerts])
