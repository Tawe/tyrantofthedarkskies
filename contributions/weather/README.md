# Weather (docs/weather_system.md)

Regional weather is defined here. The server loads:

- **transitions.json** – per weather_type, weights for next weather (e.g. `"clear": { "clear": 50, "fog": 30, "wind": 20 }`).
- **overlays.json** (optional) – per weather_type and exposure, short in-world overlay line.
- **change_messages.json** (optional) – message shown when weather changes to this type.

Rooms set `region_id` (or inherit from `zone`) and `weather_exposure`: `indoor` | `sheltered` | `outdoor` | `coastal`.
