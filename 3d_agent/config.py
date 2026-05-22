"""Configuration for the minimal 3D modeling agent.

The default mode uses a local mock parser so the example can run without
network access or an API key.

To reuse the same Microsoft EMU / copilot-api setup as the S360 agents, start
copilot-api first and set AI_PROVIDER=copilot_api. In that mode the local
copilot-api service handles account authentication, so the auth token can
remain a dummy value.
"""

import os

USE_OPENAI = os.getenv("USE_OPENAI", "false").lower() == "true"
USE_COPILOT_API = os.getenv("USE_COPILOT_API", "false").lower() == "true"

AI_PROVIDER = os.getenv("AI_PROVIDER", "").lower()
if not AI_PROVIDER:
	if USE_COPILOT_API:
		AI_PROVIDER = "copilot_api"
	elif USE_OPENAI:
		AI_PROVIDER = "openai"
	else:
		AI_PROVIDER = "mock"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

COPILOT_API_BASE_URL = os.getenv(
	"ANTHROPIC_BASE_URL",
	os.getenv("COPILOT_API_BASE_URL", "http://localhost:4141"),
).rstrip("/")
COPILOT_API_AUTH_TOKEN = os.getenv(
	"ANTHROPIC_AUTH_TOKEN",
	os.getenv("COPILOT_API_AUTH_TOKEN", "dummy"),
)
COPILOT_API_MODEL = os.getenv(
	"COPILOT_API_MODEL",
	os.getenv("ANTHROPIC_MODEL", "gpt-4.1"),
)
COPILOT_API_TIMEOUT_SECONDS = int(os.getenv("COPILOT_API_TIMEOUT_SECONDS", "60"))
