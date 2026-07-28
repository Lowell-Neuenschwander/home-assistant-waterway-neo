# Contributing

1. Fork the repository and create a focused branch.
2. Never commit live controller addresses, PubNub keys, channels, captures, or
   Home Assistant storage files.
3. Add or update tests for protocol changes.
4. Run `ruff check .`, `ruff format --check .`, and `pytest`.
5. Explain the tested controller, firmware, and redaction method in the pull
   request without publishing unique identifiers.

Decoded write commands must include evidence of both the official app request
and the controller's matching response. Guessed write commands will not be
accepted because incorrect spa control can create safety risks.
