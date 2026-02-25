# app/modules/i18n.py
"""
国际化（Internationalization）模块
支持简体中文和英式英语的动态切换
"""
import json
from pathlib import Path
from typing import Any, Dict, Optional
import streamlit as st

class I18n:
    """多语言管理类"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if I18n._initialized:
            return
            
        self.locales_dir = Path(__file__).parent.parent / "locales"
        self.translations: Dict[str, Dict] = {}
        self.current_language = "zh"  # default to Chinese
        
        # Load translation files
        self._load_translations()
        I18n._initialized = True
    
    def _load_translations(self):
        """Load all translation files"""
        for lang_file in self.locales_dir.glob("*.json"):
            lang = lang_file.stem
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[lang] = json.load(f)
            except Exception as e:
                print(f"Error loading {lang_file}: {e}")
    
    def get(self, key: str, default: str = "") -> str:
        """
        Get translated text by key
        Supports nested keys with dot notation: "nav.home"
        """
        keys = key.split('.')
        value = self.translations.get(self.current_language, {})
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        
        return value if value else default
    
    def set_language(self, lang: str):
        """Set current language"""
        if lang in self.translations:
            self.current_language = lang
            if 'language' in st.session_state:
                st.session_state.language = lang
    
    def get_language(self) -> str:
        """Get current language"""
        return self.current_language
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get all available languages with their display names"""
        langs = {}
        for lang in self.translations:
            display_name = self.translations[lang].get('language', {}).get('name', lang.upper())
            langs[lang] = display_name
        return langs


def init_i18n_session():
    """Initialize language in Streamlit session state"""
    if 'language' not in st.session_state:
        st.session_state.language = 'zh'  # Default to Chinese
    
    i18n = I18n()
    i18n.set_language(st.session_state.language)
    return i18n


def get_i18n() -> I18n:
    """Get the global I18n instance"""
    return I18n()


def t(key: str, default: str = "") -> str:
    """
    Shorthand function to get translated text
    Usage: t("nav.home")
    """
    return get_i18n().get(key, default)
