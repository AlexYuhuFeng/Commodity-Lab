from app.i18n import _resolve_path, t


def test_resolve_path_returns_none_for_non_scalar_sections():
    data = {"data_management": {"title": "Data Management"}}
    assert _resolve_path(data, "data_management") is None


def test_translation_key_alias_avoids_section_dict_stringification():
    assert t("data_management", lang="en") == "Data Management"
    assert t("data_management", lang="zh") == "数据管理"


def test_data_showcase_tab_keys_are_translated():
    assert t("data_showcase.tabs.overview", lang="en") == "Overview"
    assert t("data_showcase.tabs.overview", lang="zh") == "概览"
