# Legacy Home Assistant package

Use the HACS custom integration unless your Home Assistant installation cannot
load custom components.

## Install

1. Copy `waterway_neo.py` to `/config/waterway_neo.py`.
2. Copy `waterway_neo_config.json.example` to
   `/config/waterway_neo_config.json` and replace every example value.
3. Restrict access to the configuration file; it contains controller cloud
   credentials.
4. Copy `waterway_neo_package.yaml` to
   `/config/packages/waterway_neo.yaml`.
5. Ensure `configuration.yaml` contains:

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

6. Run **Developer tools → YAML → Check configuration**, then restart Home
   Assistant.

The package polls every five minutes, exposes temperature and clock entities,
provides target/clock shell commands, and includes an optional 104°F eight-hour
guard. Adjust entity IDs if they collide with existing helpers.
