import re


def clean_bloomberg_newsletter(text: str) -> str:
    """Return cleaned newsletter text with footers and annotations removed."""
    # Remove all URLs within angle brackets
    text = re.sub(r'<https?://[^>]+>', '', text)

    # Remove Bloomberg tracking links that occasionally contain garbled characters
    text = re.sub(r'<https://sli\.bloomberg\.com/click[^>]*>', '', text)

    # Drop stray lines that just say "Quoted"
    text = re.sub(r'^Quoted\s*\n?', '', text, flags=re.MULTILINE)

    # Remove inline annotations like [1] <> or [4] <>
    text = re.sub(r'\[\d+\]\s*<>', '', text)

    # Remove numeric inline notes: [number] + newlines or whitespace
    text = re.sub(r'\[\d+\]\s*', '', text)

    # Cut off newsletter footers and marketing sections
    footer_markers = [
        "You received this message because",
        "Subscribe to Bloomberg",
        "Want to sponsor",
        "Contact Us",
        "Bloomberg Terminal",
        "Follow Us",
        "View in browser",
        "Market Snapshot",
        "Newsletter",
        "Enjoying Markets Daily",
    ]
    for marker in footer_markers:
        if marker in text:
            text = text.split(marker)[0]

    # Clean up leftover artifacts
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{2,}', '\n\n', text)
    text = re.sub(r'^\s+|\s+$', '', text)
    return text
