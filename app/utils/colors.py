class TextColor:
    """ANSI escape codes for terminal text coloring."""

    red = "\033[91m"
    green = "\033[92m"
    yellow = "\033[93m"
    blue = "\033[94m"
    magenta = "\033[95m"
    cyan = "\033[96m"
    white = "\033[97m"
    reset = "\033[0m"
    bold = "\033[1m"


reset = TextColor.reset
bold = TextColor.bold
