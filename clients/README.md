# Plantangenet Game Dashboard Backend API

This document describes the HTTP API provided by the Plantangenet game backend for use by the dashboard frontend. The API exposes information about games, agents (players), referees, stats, and other dashboard objects.

## Base URL

The backend is typically served at:

```
http://localhost:8000/
```

## Endpoints

### `GET /dashboard/api/objects`

Returns a JSON object containing all registered dashboard objects, including players, referees, stats, and games.

#### Example Response

```json
{
  "objects": [
    {
      "id": "player:alice",
      "type": "player",
      "name": "Alice",
      "render_data": { ... }
    },
    {
      "id": "referee:main",
      "type": "referee",
      "name": "MainReferee",
      "render_data": { ... }
    },
    {
      "id": "game:1",
      "type": "game",
      "players": ["alice", "bob"],
      "state": "in_progress",
      "render_data": { ... }
    },
    {
      "id": "stats:global",
      "type": "stats",
      "games_played": 10,
      "render_data": { ... }
    }
    // ... more objects ...
  ]
}
```

#### Object Fields
- `id`: Unique identifier for the object (string)
- `type`: One of `player`, `referee`, `game`, `stats`, etc.
- `name`: (optional) Name of the object (for players, referees)
- `players`: (for games) List of player names/IDs
- `state`: (for games) Current state (e.g., `in_progress`, `finished`)
- `games_played`: (for stats) Number of games played
- `render_data`: Object-specific data for frontend rendering

### `GET /dashboard/api/assets/{asset_path}`

Serves static assets (images, etc.) referenced by dashboard objects. The `asset_path` is relative to the backend's asset directory.

### `GET /dashboard`

Serves the dashboard web interface (legacy; will be replaced by the new React app).

## Notes
- All dashboard objects must implement a `get_render_data()` method on the backend to provide their `render_data` field.
- The API is designed to be extensible: new object types can be added as needed.
- The frontend should poll or use websockets for live updates (future work).

## Example Usage
To fetch all dashboard objects:

```js
fetch('http://localhost:8000/dashboard/api/objects')
  .then(res => res.json())
  .then(data => {
    // data.objects is an array of dashboard objects
  });
```

---

For more details, see the backend code in `python/plantangenet/game/session_dashboard.py` and the example game apps in `examples/tictactoe/` and `examples/breakout/`.
