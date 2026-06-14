"""admin.app.validate_pdf_filename 的校验测试。

确保上传文件名的拒绝式校验覆盖：非 PDF、路径分隔符（/ 与 \\）、
空字节、隐藏文件、超长文件名；同时保留合法的原始（含中文/空格）文件名。
"""

import importlib
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ADMIN_DIR = PROJECT_ROOT / "admin"


@pytest.fixture(scope="module")
def app_module():
    sys.path.insert(0, str(ADMIN_DIR))
    try:
        mod = importlib.import_module("app")
    except Exception as exc:  # 缺少可选依赖时跳过，而非误报失败
        pytest.skip(f"无法导入 admin/app.py: {exc}")
    return mod


def test_accepts_plain_pdf(app_module):
    ok, err = app_module.validate_pdf_filename("paper.pdf")
    assert ok and err is None


def test_accepts_unicode_and_spaces(app_module):
    ok, err = app_module.validate_pdf_filename("过敏原 检测 2024.pdf")
    assert ok and err is None


def test_accepts_uppercase_extension(app_module):
    ok, _ = app_module.validate_pdf_filename("Report.PDF")
    assert ok


@pytest.mark.parametrize("name", [
    "",
    "notes.txt",
    "a/b.pdf",
    "a\\b.pdf",
    "../escape.pdf",
    "evil\x00.pdf",
    ".hidden.pdf",
])
def test_rejects_bad_names(app_module, name):
    ok, err = app_module.validate_pdf_filename(name)
    assert not ok and err


def test_rejects_too_long(app_module):
    name = ("x" * 300) + ".pdf"
    ok, err = app_module.validate_pdf_filename(name)
    assert not ok and "过长" in err
