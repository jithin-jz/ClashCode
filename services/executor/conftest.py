"""
Test configuration for executor service.
Forces auth to be disabled during test runs regardless of CI environment.
"""

import os

# Force-disable auth for tests (overrides CI env vars)
os.environ["INTERNAL_API_KEY"] = ""
os.environ["INTERNAL_SIGNING_SECRET"] = ""
os.environ["INTERNAL_REQUIRE_SIGNATURE"] = "false"
