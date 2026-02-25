"""
告警通知系统 - 支持Email、Telegram、Slack多渠道通知
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from datetime import datetime
from typing import List, Dict, Optional
import json


class NotificationConfig:
    """通知配置管理"""
    
    def __init__(self):
        self.channels = {}  # 存储各渠道配置
        
    def set_email(self, smtp_server: str, smtp_port: int, sender_email: str, 
                  sender_password: str):
        """配置Email通知"""
        self.channels['email'] = {
            'type': 'email',
            'smtp_server': smtp_server,
            'smtp_port': smtp_port,
            'sender_email': sender_email,
            'sender_password': sender_password,
            'enabled': True
        }
        
    def set_telegram(self, bot_token: str, chat_id: str):
        """配置Telegram通知"""
        self.channels['telegram'] = {
            'type': 'telegram',
            'bot_token': bot_token,
            'chat_id': chat_id,
            'enabled': True
        }
        
    def set_slack(self, webhook_url: str):
        """配置Slack通知"""
        self.channels['slack'] = {
            'type': 'slack',
            'webhook_url': webhook_url,
            'enabled': True
        }
        
    def disable_channel(self, channel_type: str):
        """禁用特定通知渠道"""
        if channel_type in self.channels:
            self.channels[channel_type]['enabled'] = False
            
    def get_active_channels(self) -> List[str]:
        """获取所有启用的通知渠道"""
        return [ch for ch, cfg in self.channels.items() if cfg.get('enabled', False)]


class AlertNotifier:
    """告警通知发送器"""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
        
    def notify(self, alert_info: Dict, channels: Optional[List[str]] = None) -> Dict:
        """
        发送告警通知到指定渠道
        
        Args:
            alert_info: {
                'rule_name': '规则名',
                'ticker': '商品代码',
                'severity': 'high|medium|low',
                'message': '告警详情',
                'value': '触发值',
                'threshold': '阈值',
                'timestamp': '时间戳'
            }
            channels: 目标渠道列表，None表示所有启用的渠道
            
        Returns:
            {'success': bool, 'results': {'channel': status}}
        """
        if channels is None:
            channels = self.config.get_active_channels()
            
        results = {}
        for channel in channels:
            if channel not in self.config.channels:
                results[channel] = {'success': False, 'error': 'Channel not configured'}
                continue
                
            try:
                if channel == 'email':
                    results[channel] = self._send_email(alert_info)
                elif channel == 'telegram':
                    results[channel] = self._send_telegram(alert_info)
                elif channel == 'slack':
                    results[channel] = self._send_slack(alert_info)
            except Exception as e:
                results[channel] = {'success': False, 'error': str(e)}
                
        return {
            'success': all(r.get('success') for r in results.values()),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
    def _send_email(self, alert_info: Dict) -> Dict:
        """发送Email通知"""
        config = self.config.channels.get('email', {})
        
        try:
            # 构建邮件内容
            subject = f"【ALERT】 {alert_info.get('rule_name', 'Unknown')} - {alert_info.get('ticker')}"
            
            body = self._format_alert_message(alert_info)
            
            # 发送邮件
            msg = MIMEMultipart()
            msg['From'] = config['sender_email']
            msg['To'] = config['sender_email']  # 默认发给自己
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
                server.starttls()
                server.login(config['sender_email'], config['sender_password'])
                server.send_message(msg)
                
            return {'success': True, 'message': 'Email sent successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def _send_telegram(self, alert_info: Dict) -> Dict:
        """发送Telegram通知"""
        config = self.config.channels.get('telegram', {})
        
        try:
            message = self._format_telegram_message(alert_info)
            
            url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
            data = {
                'chat_id': config['chat_id'],
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            return {'success': True, 'message': 'Telegram message sent successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def _send_slack(self, alert_info: Dict) -> Dict:
        """发送Slack通知"""
        config = self.config.channels.get('slack', {})
        
        try:
            payload = self._format_slack_message(alert_info)
            
            response = requests.post(
                config['webhook_url'],
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            return {'success': True, 'message': 'Slack message sent successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    @staticmethod
    def _format_alert_message(alert_info: Dict) -> str:
        """格式化Email通知内容"""
        severity_color = {
            'high': '#FF0000',
            'medium': '#FFA500',
            'low': '#0066CC'
        }
        color = severity_color.get(alert_info.get('severity', 'low'), '#0066CC')
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="border-left: 4px solid {color}; padding: 10px; background-color: #f5f5f5;">
                <h2 style="margin: 0 0 10px 0; color: {color};">
                    🚨 告警通知
                </h2>
                <table style="width: 100%;">
                    <tr>
                        <td style="padding: 5px;"><strong>规则名称:</strong></td>
                        <td style="padding: 5px;">{alert_info.get('rule_name', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px;"><strong>商品代码:</strong></td>
                        <td style="padding: 5px;">{alert_info.get('ticker', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px;"><strong>严重程度:</strong></td>
                        <td style="padding: 5px; color: {color}; font-weight: bold;">
                            {alert_info.get('severity', 'N/A').upper()}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 5px;"><strong>当前值:</strong></td>
                        <td style="padding: 5px;">{alert_info.get('value', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px;"><strong>阈值:</strong></td>
                        <td style="padding: 5px;">{alert_info.get('threshold', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px;"><strong>详情:</strong></td>
                        <td style="padding: 5px;">{alert_info.get('message', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px;"><strong>时间:</strong></td>
                        <td style="padding: 5px;">{alert_info.get('timestamp', datetime.now().isoformat())}</td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """
        return html
        
    @staticmethod
    def _format_telegram_message(alert_info: Dict) -> str:
        """格式化Telegram通知内容"""
        severity_emoji = {
            'high': '🔴',
            'medium': '🟠',
            'low': '🔵'
        }
        emoji = severity_emoji.get(alert_info.get('severity', 'low'), '🔵')
        
        message = f"""
<b>{emoji} 告警通知</b>

<b>规则:</b> {alert_info.get('rule_name', 'N/A')}
<b>商品:</b> {alert_info.get('ticker', 'N/A')}
<b>严重:</b> <b>{alert_info.get('severity', 'N/A').upper()}</b>
<b>当前值:</b> {alert_info.get('value', 'N/A')}
<b>阈值:</b> {alert_info.get('threshold', 'N/A')}
<b>详情:</b> {alert_info.get('message', 'N/A')}
<b>时间:</b> {alert_info.get('timestamp', datetime.now().isoformat())}
        """
        return message.strip()
        
    @staticmethod
    def _format_slack_message(alert_info: Dict) -> Dict:
        """格式化Slack通知内容"""
        severity_color = {
            'high': 'danger',
            'medium': 'warning',
            'low': 'good'
        }
        color = severity_color.get(alert_info.get('severity', 'low'), 'good')
        
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"告警: {alert_info.get('rule_name', 'Unknown')}",
                    "fields": [
                        {
                            "title": "商品代码",
                            "value": alert_info.get('ticker', 'N/A'),
                            "short": True
                        },
                        {
                            "title": "严重程度",
                            "value": alert_info.get('severity', 'N/A').upper(),
                            "short": True
                        },
                        {
                            "title": "当前值",
                            "value": str(alert_info.get('value', 'N/A')),
                            "short": True
                        },
                        {
                            "title": "阈值",
                            "value": str(alert_info.get('threshold', 'N/A')),
                            "short": True
                        },
                        {
                            "title": "详情",
                            "value": alert_info.get('message', 'N/A'),
                            "short": False
                        },
                        {
                            "title": "触发时间",
                            "value": alert_info.get('timestamp', datetime.now().isoformat()),
                            "short": False
                        }
                    ]
                }
            ]
        }
        return payload


class NotificationHistory:
    """通知历史记录管理"""
    
    def __init__(self, db_connection=None):
        """
        初始化通知历史
        
        Args:
            db_connection: 数据库连接对象 (可选)
        """
        self.db = db_connection
        self.history = []  # 内存缓冲
        
    def add_record(self, notification_result: Dict):
        """添加通知记录"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'result': notification_result
        }
        self.history.append(record)
        
        # 如果有数据库连接，保存到数据库
        if self.db:
            self._save_to_db(record)
            
    def _save_to_db(self, record: Dict):
        """保存到数据库 (需要在db.py中定义表和函数)"""
        # TODO: 实现数据库保存逻辑
        pass
        
    def get_history(self, limit: int = 100) -> List[Dict]:
        """获取最近的通知记录"""
        return self.history[-limit:]
        
    def get_failed_notifications(self) -> List[Dict]:
        """获取失败的通知"""
        return [r for r in self.history if not r['result'].get('success')]
        
    def retry_failed(self, notifier: AlertNotifier) -> Dict:
        """重试失败的通知"""
        failed = self.get_failed_notifications()
        results = {}
        
        for record in failed:
            # 重试逻辑 (可根据需要调整)
            results[record['timestamp']] = 'pending_retry'
            
        return results


class Notifier(AlertNotifier):
    """Backward-compatible alias for older imports."""
    pass
