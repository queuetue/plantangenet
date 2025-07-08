# Plantangenet Game Dashboard (React/Vite)

This directory contains the modern React/Vite frontend for the Plantangenet Game Dashboard. The dashboard provides a real-time, interactive view of all games, agents (players), referees, stats, and other objects managed by the Plantangenet backend.

## Features
- Displays all registered dashboard objects: games, players, referees, stats, and more
- Fetches data from the backend API (`/dashboard/api/objects`)
- Modern, responsive UI built with React and Vite
- Extensible: supports new object types and render data
- (Planned) Live updates via polling or WebSockets

## Getting Started

### Prerequisites
- Node.js (v18+ recommended)
- npm or yarn

### Install dependencies
```sh
npm install
# or
yarn install
```

### Start the development server
```sh
npm run dev
# or
yarn dev
```

The dashboard will be available at `http://localhost:5173/` (default Vite port).

### Build for production
```sh
npm run build
# or
yarn build
```

### Preview production build
```sh
npm run preview
# or
yarn preview
```

## API Integration
The frontend fetches dashboard objects from the backend API:

- **Endpoint:** `GET http://localhost:8000/dashboard/api/objects`
- **Response:** JSON array of objects (see `../README.md` for schema)

Example fetch:
```js
fetch('http://localhost:8000/dashboard/api/objects')
  .then(res => res.json())
  .then(data => {
    // data.objects is an array of dashboard objects
  });
```

## Project Structure
- `src/` — React components, pages, and logic
- `public/` — Static assets
- `vite.config.js` — Vite configuration

## Customization
- To support new object types, add new React components for their `render_data`.
- The dashboard UI is designed to be extensible and modular.

## Development Notes
- The backend must be running and accessible at `http://localhost:8000/` for API calls to succeed.
- For API details, see `../README.md` and backend code in `python/plantangenet/game/session_dashboard.py`.

## License
See root `LICENSE.md`.
