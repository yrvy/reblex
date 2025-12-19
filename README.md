# Reblex

A Python Roblox launcher with a modern GUI, built with pywebview + React.

Inspired by [voxel](https://github.com/6E6B/voxel) and [rolauncher](https://github.com/miukyo/rolauncher).

![Screenshot](screenshot.png)

## Features

- **Modern UI**: Clean, dark-themed interface built with React + Tailwind
- **Authentication**: Login with your `.ROBLOSECURITY` cookie
- **Game Search**: Search games by Place ID
- **Server Browser**: View and join specific servers
- **Game Launching**: Launch games with proper auth tickets

## Installation

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Install frontend dependencies and build

```bash
cd frontend
npm install
npm run build
cd ..
```

### 3. Run the app

```bash
python backend/main.py
```

Or install and run:

```bash
pip install -e .
reblex
```

## Development

Run frontend dev server and backend in dev mode:

```bash
# Terminal 1: Frontend
cd frontend
npm run dev

# Terminal 2: Backend (with DEV=1 to connect to Vite dev server)
set DEV=1  # Windows
export DEV=1  # Linux/Mac
python backend/main.py
```

## Project Structure

```
reblex/
├── backend/
│   ├── main.py              # Pywebview app entry point
│   └── reblex/              # Python Roblox API client
│       ├── http.py          # HTTP client with CSRF handling
│       ├── auth.py          # Authentication service
│       ├── games.py         # Game info & servers
│       ├── client.py        # Main client wrapper
│       └── launcher.py      # Player launcher
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main React app
│   │   ├── api.ts           # Pywebview API bridge
│   │   └── pages/           # UI pages
│   ├── package.json
│   └── vite.config.ts
├── pyproject.toml
└── requirements.txt
```

## How It Works

1. **Pywebview**: Creates a native window with an embedded web view
2. **React Frontend**: Modern UI that calls Python methods via `window.pywebview.api`
3. **Python Backend**: Handles Roblox API calls:
   - CSRF token from `auth.roblox.com`
   - Auth ticket from `auth.roblox.com/v1/authentication-ticket`
   - Game info from `games.roblox.com`
   - Server list from `games.roblox.com/v1/games/{id}/servers/Public`
4. **Launch**: Builds `roblox-player://` URL and opens via system handler

## Requirements

- Python 3.10+
- Node.js 18+ (for building frontend)
- Windows (for launching Roblox)
- Roblox installed

## License

MIT
