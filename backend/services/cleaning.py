import re

def clean_bloomberg_newsletter(text: str) -> str:
    """Remove angle-bracketed content and cut text at common Bloomberg footer lines."""
    # Nuke anything in angle brackets
    text = re.sub(r'<[^>]+>', '', text)

    # Drop standalone "Quoted" lines often added by Gmail
    text = re.sub(r'^Quoted\n?', '', text, flags=re.MULTILINE)

    # Define cut-off markers – all case-insensitive
    footer_markers = [
        "Got a tip or want to send in questions?",
        "Abonnieren Sie Bloomberg.com",
        "Möchten Sie Sponsor dieses Newsletters",
        "Have a tip that we should investigate?",
        "Like Supply Lines?",
        "Follow Us",
        "Get the newsletter",
        "Like getting this newsletter?"
    ]

    for marker in footer_markers:
        pattern = re.compile(re.escape(marker), re.IGNORECASE)
        match = pattern.search(text)
        if match:
            text = text[:match.start()]
            break
    return text.strip()