import pytest
from backend.services.cleaning import clean_bloomberg_newsletter


def test_remove_tracking_links_and_quoted_lines():
    messy = (
        "Market update\n"
        "<https://sli.bloomberg.com/click?foo>\n"
        "Quoted\n"
        "This is the rest"
    )
    cleaned = clean_bloomberg_newsletter(messy)
    assert "sli.bloomberg.com" not in cleaned
    assert "Quoted" not in cleaned
    assert "Market update" in cleaned
    assert "This is the rest" in cleaned
