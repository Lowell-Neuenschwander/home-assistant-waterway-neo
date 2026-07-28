# Home Assistant Waterway NEO

Unofficial Home Assistant support for Waterway Plastics NEO/Oasis spa and pool
Wi-Fi controllers.

The integration combines the controller's local `status.xml` telemetry with the
same PubNub command channel used by the Waterway mobile app. It was developed
and validated against a controller reporting Wi-Fi `1.07`, controller `C70.03`,
and panel `P0.02`. Other firmware should be treated as untested until confirmed.

> [!WARNING]
> This is an independent community project. It is not affiliated with or
> supported by Waterway Plastics. A spa is safety-critical equipment: retain the
> physical controls, manufacturer safeguards, and official app. Never rely on
> Home Assistant as the only temperature or freeze-protection mechanism.

## Features

- Local water-temperature and controller-connectivity monitoring
- Native Home Assistant climate entity with an 80–104°F target range
- Target temperature, controller clock, clock drift, and cloud-health sensors
- Manual clock synchronization button
- Optional automatic clock correction using the configured IANA time zone
- Five-minute default polling interval
- Credentials redacted from Home Assistant diagnostics
- Sanitized legacy YAML package for advanced users

## Installation with HACS

Until this repository is accepted into the HACS default catalog, add it as a
custom repository:

1. In HACS, open the three-dot menu and select **Custom repositories**.
2. Add `https://github.com/Lowell-Neuenschwander/home-assistant-waterway-neo`.
3. Select category **Integration**, download **Waterway NEO**, and restart Home
   Assistant.
4. Go to **Settings → Devices & services → Add integration** and search for
   **Waterway NEO**.

## Configuration

The setup form validates both the local controller and its cloud channel before
creating the config entry.

| Field | Purpose |
| --- | --- |
| Controller address | Reserved LAN IP or hostname; do not include a URL path |
| Publish key | PubNub publish key used by the Waterway app |
| Subscribe key | PubNub subscribe key used by the Waterway app |
| Controller channel | Controller-specific PubNub channel |
| IANA time zone | For example, `America/Denver` |
| Polling interval | 300 seconds is recommended |
| Clock correction | Corrects drift greater than the selected threshold |

The three PubNub values are not shown in the app UI. See
[Credential discovery](docs/credential-discovery.md) before setup.

## Entities

- `climate.<device>` — current and target temperature; target control
- `sensor.<device>_water_temperature`
- `sensor.<device>_target_temperature`
- `sensor.<device>_controller_time`
- `sensor.<device>_clock_drift`
- `binary_sensor.<device>_controller_connection`
- `binary_sensor.<device>_cloud_connection`
- `binary_sensor.<device>_clock_synchronized`
- `button.<device>_synchronize_clock`

Entity IDs are assigned by Home Assistant and may differ from these examples.

## Eight-hour 104°F safeguard

The integration deliberately exposes ordinary Home Assistant entities rather
than silently imposing a household temperature schedule. A tested example that
returns a 104°F target to 99°F after eight hours is provided in
[`examples/automations.yaml`](examples/automations.yaml). Review the entity IDs
and temperatures before importing it.

Because the default polling interval is five minutes, a target selected in the
Waterway app can take up to five minutes to appear in Home Assistant.

## Legacy package

The custom integration is preferred. Users who cannot install HACS can use the
standalone files in [`legacy/`](legacy/README.md). Credentials live in an
untracked JSON file rather than in the package or helper source.

## Security and privacy

- Never post PubNub keys or the controller channel in an issue, screenshot, or
  diagnostics attachment.
- Keep the controller on a trusted or appropriately firewalled IoT network.
- Do not expose `status.xml` or the controller web interface to the internet.
- The integration communicates locally over HTTP and with PubNub over HTTPS.
- See [SECURITY.md](SECURITY.md) for private vulnerability reporting.

## Current limitations

- Target changes and clock operations require the Waterway/PubNub cloud path.
- Automatic discovery and credential onboarding are not yet available.
- Pump, light, filtration, and auxiliary controls have not been safely decoded
  and therefore are intentionally not exposed.
- Only the firmware combination listed above has been validated so far.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md). Pull requests should pass Ruff, pytest,
HACS validation, and hassfest. Protocol additions require a captured request and
matching controller response with all credentials and identifiers removed.

## License

[MIT](LICENSE)
