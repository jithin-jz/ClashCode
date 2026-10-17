import os

# Per-stream cap for learner program output; the run is stopped once exceeded.
OUTPUT_LIMIT_BYTES = int(os.getenv("EXECUTOR_OUTPUT_LIMIT_BYTES", str(32 * 1024)))
