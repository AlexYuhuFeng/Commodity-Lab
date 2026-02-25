"""
定时告警检测调度器 - 后台自动检测告警规则
支持：Streamlit session state, 线程池，完整生命周期管理
"""
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, List
import streamlit as st
from pathlib import Path
import sys

# Add workspace root to path
workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))

from core.db import (
    list_alert_rules, create_alert_event, list_alert_events,
    get_db_connection, acknowledge_alert_event
)
from core.condition_builder import ConditionEvaluator
import pandas as pd
import numpy as np


class AlertScheduler:
    """告警检测调度器 - 定时扫描和评估告警规则"""
    
    def __init__(self, check_interval: int = 300):
        """
        初始化调度器
        
        参数:
            check_interval: 检测间隔(秒)，默认5分钟
        """
        self.check_interval = check_interval
        self.is_running = False
        self.thread = None
        self.last_check_time = None
        self.check_count = 0
        self.errors_count = 0
        self.triggered_alerts = []
        self.lock = threading.Lock()
        
    def start(self):
        """启动后台调度线程"""
        if self.is_running:
            return
            
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        """停止调度线程"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
            
    def _run_loop(self):
        """后台执行循环"""
        while self.is_running:
            try:
                self.check_all_rules()
                time.sleep(self.check_interval)
            except Exception as e:
                with self.lock:
                    self.errors_count += 1
                print(f"Scheduler error: {e}")
                time.sleep(self.check_interval)
                
    def check_all_rules(self) -> Dict:
        """
        检查所有已启用的告警规则
        
        返回:
            检查结果统计
        """
        try:
            with self.lock:
                self.check_count += 1
                self.last_check_time = datetime.now()
                
            # 获取所有启用的规则
            rules = list_alert_rules(enabled_only=True)
            if not rules:
                return {"total": 0, "triggered": 0, "errors": []}
                
            triggered = 0
            errors = []
            new_alerts = []
            
            for rule in rules:
                try:
                    result = self._evaluate_rule(rule)
                    if result["triggered"]:
                        # 创建告警事件
                        create_alert_event(
                            rule_id=rule['rule_id'],
                            ticker=rule['ticker'],
                            severity=rule['severity'],
                            message=result['message'],
                            value=result['value']
                        )
                        triggered += 1
                        new_alerts.append({
                            'rule_id': rule['rule_id'],
                            'ticker': rule['ticker'],
                            'message': result['message'],
                            'severity': rule['severity'],
                            'created_at': datetime.now().isoformat()
                        })
                except Exception as e:
                    errors.append({
                        'rule_id': rule['rule_id'],
                        'error': str(e)
                    })
                    
            # 更新触发列表
            with self.lock:
                self.triggered_alerts = new_alerts
                
            return {
                "total_rules": len(rules),
                "triggered": triggered,
                "errors": errors,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            with self.lock:
                self.errors_count += 1
            raise
            
    def _evaluate_rule(self, rule: Dict) -> Dict:
        """
        评估单个规则
        
        参数:
            rule: 规则配置字典
            
        返回:
            {
                'triggered': bool,
                'message': str,
                'value': float
            }
        """
        rule_type = rule.get('rule_type')
        ticker = rule.get('ticker')
        threshold = rule.get('threshold', 0)
        condition_expr = rule.get('condition_expr', '')
        
        try:
            # 从数据库获取最新数据
            conn = get_db_connection()
            
            # 获取价格数据
            price_query = f"""
                SELECT date, close, volume 
                FROM prices_daily 
                WHERE ticker = '{ticker}' 
                ORDER BY date DESC 
                LIMIT 100
            """
            prices_df = pd.read_sql(price_query, conn)
            
            if prices_df.empty:
                return {"triggered": False, "message": "No data", "value": 0}
                
            conn.close()
            
            # 根据规则类型评估
            if rule_type == "price_threshold":
                latest_price = prices_df.iloc[0]['close']
                triggered = latest_price > threshold
                message = f"Price {latest_price:.2f} > threshold {threshold:.2f}"
                value = latest_price
                
            elif rule_type == "zscore":
                prices = prices_df['close'].values[:20]
                if len(prices) < 5:
                    return {"triggered": False, "message": "Insufficient data", "value": 0}
                mean = np.mean(prices)
                std = np.std(prices)
                if std == 0:
                    return {"triggered": False, "message": "No variance", "value": 0}
                latest_price = prices_df.iloc[0]['close']
                z_score = abs((latest_price - mean) / std)
                triggered = z_score > threshold
                message = f"Z-score {z_score:.2f} > threshold {threshold:.2f}"
                value = z_score
                
            elif rule_type == "volatility":
                prices = prices_df['close'].values[:251]  # 近1年数据
                if len(prices) < 20:
                    return {"triggered": False, "message": "Insufficient historical data", "value": 0}
                returns = np.diff(np.log(prices))
                annual_volatility = np.std(returns) * np.sqrt(252)
                triggered = annual_volatility > threshold
                message = f"Volatility {annual_volatility:.4f} > threshold {threshold:.4f}"
                value = annual_volatility
                
            elif rule_type == "data_staleness":
                latest_date = pd.to_datetime(prices_df.iloc[0]['date'])
                days_since = (datetime.now() - latest_date).days
                triggered = days_since > threshold
                message = f"Data staleness {days_since} days > threshold {threshold} days"
                value = days_since
                
            elif rule_type == "data_missing":
                # 检查缺失数据百分比
                expected_count = len(prices_df)
                actual_count = len(prices_df.dropna(subset=['close']))
                missing_pct = (1 - actual_count / expected_count) * 100 if expected_count > 0 else 0
                triggered = missing_pct > threshold
                message = f"Missing data {missing_pct:.1f}% > threshold {threshold:.1f}%"
                value = missing_pct
                
            elif rule_type == "custom":
                # 自定义表达式评估
                evaluator = ConditionEvaluator()
                latest_price = prices_df.iloc[0]['close']
                context = {
                    'price': latest_price,
                    'threshold': threshold,
                    'mean': np.mean(prices_df['close'].values[:20]),
                    'std': np.std(prices_df['close'].values[:20])
                }
                result = evaluator.evaluate(condition_expr, context)
                triggered = bool(result)
                message = f"Custom expression evaluated: {result}"
                value = float(result) if isinstance(result, (int, float)) else 0
                
            else:
                return {"triggered": False, "message": "Unknown rule type", "value": 0}
                
            return {
                "triggered": triggered,
                "message": message,
                "value": value
            }
            
        except Exception as e:
            return {
                "triggered": False,
                "message": f"Evaluation error: {str(e)}",
                "value": 0
            }
            
    def get_status(self) -> Dict:
        """获取调度器状态"""
        with self.lock:
            return {
                'is_running': self.is_running,
                'check_count': self.check_count,
                'errors_count': self.errors_count,
                'last_check_time': self.last_check_time.isoformat() if self.last_check_time else None,
                'check_interval': self.check_interval,
                'triggered_alerts': len(self.triggered_alerts),
                'latest_alerts': self.triggered_alerts[:10]  # 最近10个
            }
            
    def get_recent_alerts(self, limit: int = 50) -> List[Dict]:
        """获取最近的触发告警"""
        with self.lock:
            return self.triggered_alerts[:limit]
            
    def reset_stats(self):
        """重置统计数据"""
        with self.lock:
            self.check_count = 0
            self.errors_count = 0
            self.triggered_alerts = []
            self.last_check_time = None


# 全局调度器实例
_global_scheduler = None


def get_scheduler(check_interval: int = 300) -> AlertScheduler:
    """获取全局调度器实例（单例模式）"""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = AlertScheduler(check_interval)
    return _global_scheduler


def init_scheduler_state():
    """在Streamlit中初始化调度器状态"""
    if 'alert_scheduler' not in st.session_state:
        st.session_state.alert_scheduler = get_scheduler()
        st.session_state.scheduler_running = False
        st.session_state.check_interval = 300  # 默认5分钟


def toggle_scheduler(enabled: bool, check_interval: int = 300):
    """启用/禁用调度器"""
    init_scheduler_state()
    scheduler = st.session_state.alert_scheduler
    scheduler.check_interval = check_interval
    
    if enabled and not st.session_state.scheduler_running:
        scheduler.start()
        st.session_state.scheduler_running = True
    elif not enabled and st.session_state.scheduler_running:
        scheduler.stop()
        st.session_state.scheduler_running = False


def get_scheduler_status() -> Dict:
    """获取调度器状态"""
    init_scheduler_state()
    return st.session_state.alert_scheduler.get_status()
