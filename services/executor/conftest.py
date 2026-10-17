"""
Test configuration for executor service.
Disables auth for the API tests regardless of CI environment; auth itself is
covered by tests that flip these variables explicitly.
"""

import os

os.environ["EXECUTOR_ALLOW_UNAUTHENTICATED"] = "true"
os.environ["EXECUTOR_API_KEY"] = ""
os.environ["EXECUTOR_SIGNING_SECRET"] = ""
os.environ["INTERNAL_API_KEY"] = ""
os.environ["INTERNAL_SIGNING_SECRET"] = ""
