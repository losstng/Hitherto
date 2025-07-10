from backend.services.utils import safe_filename


def test_safe_filename_sanitizes_invalid_chars():
    assert safe_filename('morning:briefing*europe') == 'morning_briefing_europe'

