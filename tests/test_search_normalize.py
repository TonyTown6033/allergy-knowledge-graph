r"""graph_view.server 搜索归一化的回归测试。

重点防回归：_SEARCH_CLEAN_RE 曾被双重转义（r"[\\s..." 而非 r"[\s..."），
导致 _normalize_search_text 对空白/标点/分隔符完全不生效，
"过敏 原" 无法命中 "过敏原"。
"""

import importlib
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GRAPH_VIEW = PROJECT_ROOT / "graph_view"


@pytest.fixture(scope="module")
def server():
    sys.path.insert(0, str(GRAPH_VIEW))
    try:
        mod = importlib.import_module("server")
    except Exception as exc:  # 缺少可选依赖时跳过，而非误报失败
        pytest.skip(f"无法导入 graph_view/server.py: {exc}")
    return mod


def test_normalize_strips_separators_and_punctuation(server):
    # 空格、连字符、斜杠、全角括号、中英文标点都应被移除
    assert server._normalize_search_text("过敏 原-检/测") == "过敏原检测"
    assert server._normalize_search_text("IgE（特异性）抗体") == "ige特异性抗体"


def test_normalize_lowercases(server):
    assert server._normalize_search_text("Allergy") == "allergy"


def test_normalize_removes_stopwords(server):
    # "相关" 属于停用词；归一化后应等价于去掉分隔符与停用词的结果
    assert server._normalize_search_text("过敏 相关 检测") == "过敏检测"


def test_normalize_keeps_english_letter_s(server):
    # 回归点：旧的错误正则会把字母 s 当作匹配项之一，这里确保 s 不被吞掉
    assert server._normalize_search_text("strains") == "strains"


def test_normalize_handles_empty(server):
    assert server._normalize_search_text("") == ""
    assert server._normalize_search_text(None) == ""


def test_clean_regex_matches_whitespace(server):
    # 直接验证正则本身：必须能匹配空白字符
    assert server._SEARCH_CLEAN_RE.search(" ") is not None
    assert server._SEARCH_CLEAN_RE.search("\t") is not None
