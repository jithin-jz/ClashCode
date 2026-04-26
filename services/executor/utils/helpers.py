import os

OUTPUT_LIMIT_BYTES = int(os.getenv("EXECUTOR_OUTPUT_LIMIT_BYTES", str(32 * 1024)))


def truncate_output(value: str) -> str:
    if not value:
        return ""
    encoded = value.encode("utf-8", errors="replace")
    if len(encoded) <= OUTPUT_LIMIT_BYTES:
        return value
    truncated = encoded[:OUTPUT_LIMIT_BYTES].decode("utf-8", errors="replace")
    return f"{truncated}\n...[output truncated]"
