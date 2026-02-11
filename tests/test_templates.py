import pytest
from pwd_generator.templates import (
    PasswordTemplate,
    get_template,
    list_templates,
    TEMPLATES,
)


def test_password_template_generation():
    template = PasswordTemplate(
        name="test",
        uppercase=True,
        lowercase=True,
        digits=True,
        special=True,
        min_length=8,
    )
    pwd = template.generate(12)
    assert len(pwd) == 12
    assert any(c.isupper() for c in pwd)
    assert any(c.islower() for c in pwd)
    assert any(c.isdigit() for c in pwd)
    assert any(c in "@#$!?^&*~()[]=-_." for c in pwd)


def test_password_template_exclude_chars():
    template = PasswordTemplate(
        name="no_ambiguous", exclude_chars="0O1lI", min_length=8
    )
    for _ in range(10):
        pwd = template.generate(12)
        assert not any(c in "0O1lI" for c in pwd)


def test_password_template_custom_special():
    template = PasswordTemplate(
        name="custom",
        custom_special="!@",
        uppercase=False,
        lowercase=False,
        digits=False,
        min_length=4,
    )
    pwd = template.generate(4)
    assert all(c in "!@" for c in pwd)


def test_password_template_min_length_enforcement():
    template = PasswordTemplate(name="min", min_length=10)
    pwd = template.generate(5)
    assert len(pwd) == 10


def test_get_template():
    t = get_template("alphanumeric")
    assert t is not None
    assert t.name == "alphanumeric"

    assert get_template("nonexistent") is None


def test_list_templates():
    templates = list_templates()
    assert "alphanumeric" in templates
    assert "numeric_only" in templates
    assert len(templates) == len(TEMPLATES)


def test_invalid_template():
    with pytest.raises(ValueError):
        PasswordTemplate(
            name="invalid",
            uppercase=False,
            lowercase=False,
            digits=False,
            special=False,
        )
