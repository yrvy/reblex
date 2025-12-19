# Reblex

A Python Roblox launcher that handles authentication, game joining, and player launching through the Roblox API.

Inspired by [voxel](https://github.com/6E6B/voxel).

## Features

- **Authentication**: Login with your `.ROBLOSECURITY` cookie
- **Game Info**: Fetch game details (name, players, visits, etc.)
- **Server Browser**: List available servers with player counts
- **Game Launching**: Join games via the Roblox API with proper auth tickets
- **Async**: Built on `aiohttp` for efficient API calls

## Installation

```bash
pip install -e .
```

Or with requirements:

```bash
pip install -r requirements.txt
```

## Usage

### CLI

```bash
# Login (saves cookie to ~/.reblex/cookie)
reblex login

# Or login with cookie directly
reblex login "YOUR_ROBLOSECURITY_COOKIE"

# Show current user
reblex whoami

# Get game info
reblex info 123456789

# List servers
reblex servers 123456789
reblex servers 123456789 --limit 25

# Launch game (joins any server)
reblex launch 123456789

# Join specific server by Job ID
reblex launch 123456789 --server "abc123-job-id"

# Join server by index (0 = most players)
reblex join-server 123456789 0
```

### As a Library

```python
import asyncio
from reblex import RobloxClient, RobloxLauncher

async def main():
    cookie = "your_.ROBLOSECURITY_cookie"

    async with RobloxClient(cookie) as client:
        # Get authenticated user
        user = await client.get_user()
        print(f"Logged in as {user.username}")

        # Get game info
        game = await client.get_game_info(123456789)
        print(f"Game: {game.name} ({game.playing} playing)")

        # List servers
        servers = await client.get_servers(123456789, limit=10)
        for server in servers:
            print(f"Server {server.job_id}: {server.playing} players")

        # Launch a game
        launcher = RobloxLauncher(client)
        result = await launcher.launch(123456789)
        print(result.message)

asyncio.run(main())
```

## How It Works

1. **Authentication**: Uses your `.ROBLOSECURITY` cookie to authenticate with Roblox
2. **CSRF Token**: Fetches CSRF token from `auth.roblox.com` (required for POST requests)
3. **Auth Ticket**: Gets an authentication ticket from `auth.roblox.com/v1/authentication-ticket`
4. **Launch URL**: Builds a `roblox-player://` protocol URL with the auth ticket
5. **Player Launch**: Opens the URL via OS protocol handler or direct exe launch

## API Endpoints Used

| Purpose | Endpoint |
|---------|----------|
| CSRF Token | `auth.roblox.com/v2/login` (403 response) |
| Auth Ticket | `auth.roblox.com/v1/authentication-ticket` |
| User Info | `users.roblox.com/v1/users/authenticated` |
| Universe ID | `apis.roblox.com/universes/v1/places/{id}/universe` |
| Game Info | `games.roblox.com/v1/games?universeIds={id}` |
| Servers | `games.roblox.com/v1/games/{id}/servers/Public` |
| Join Game | `gamejoin.roblox.com/v1/join-game` |

## Project Structure

```
reblex/
├── main.py              # Entry point
├── reblex/
│   ├── __init__.py      # Package exports
│   ├── http.py          # HTTP client with CSRF handling
│   ├── auth.py          # Authentication service
│   ├── games.py         # Game info & servers
│   ├── client.py        # Main client wrapper
│   ├── launcher.py      # Player launcher
│   └── cli.py           # Command-line interface
├── pyproject.toml
└── requirements.txt
```

## Requirements

- Python 3.10+
- Windows (for launching Roblox)
- Roblox installed
- Valid `.ROBLOSECURITY` cookie

## License

MIT
