# Changelog

All notable changes to this project will be documented here.

## 0.1.0 — unreleased

- Add HACS-compatible Waterway NEO custom integration.
- Add native climate, temperature, connectivity, controller-time, clock-drift,
  and clock-synchronization entities.
- Add verified S3 target-temperature and S6 clock-control support.
- Add configurable 110°F high-temperature and 60°F freeze-risk warning entities.
- Document the native adjustable 80–104°F climate control and alert automations.
- Add optional automatic clock correction and five-minute default polling.
- Add redacted diagnostics, examples, tests, CI validation, and a sanitized
  legacy package.
- Keep local monitoring and cloud target control available independently.
- Verify target-temperature commands and retry unconfirmed writes.
- Add channel recovery diagnostics and a restart-safe setback watchdog example.
- Start the eight-hour setback safeguard for every target above 99°F.
