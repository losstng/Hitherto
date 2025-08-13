import os

def load_system_prompt(path: str = None) -> str:
    # Default to militant dispatch prompt location
    prompt_path = path or os.path.join(
        os.path.dirname(__file__),
        '../../agents/Dispatch/SystemPrompt.txt'
    )
    prompt_path = os.path.abspath(prompt_path)
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"System prompt file not found: {prompt_path}")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()
