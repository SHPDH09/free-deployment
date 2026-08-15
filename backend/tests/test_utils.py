import re

from app.core.deps import slugify


def test_slugify_basic():
    assert slugify("My Project") == "my-project"


def test_slugify_special_chars():
    assert slugify("Hello World!") == "hello-world"


def test_slugify_empty_fallback():
    assert slugify("!!!") == "project"
