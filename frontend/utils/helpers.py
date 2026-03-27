from datetime import datetime

def format_timestamp(timestamp: float) -> str:
    """Convert a UNIX timestamp to a readable datetime string."""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def validate_stream_url(url: str) -> bool:
    """Basic validation for stream URLs."""
    return url.startswith("http://") or url.startswith("https://") or url.startswith("rtmp://")
