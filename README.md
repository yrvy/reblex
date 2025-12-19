# Reblex

A Python Roblox launcher that handles `roblox-player://` protocol URLs directly, without needing the official Roblox bootstrapper.

## Features

- Launch Roblox games from protocol URLs (`roblox-player://`)
- Auto-detect Roblox installation
- Register as the default protocol handler
- Launch specific places by ID
- Support for Roblox Studio

## Requirements

- Python 3.10+
- Windows (for Roblox client)
- Roblox installed

## Installation

```bash
git clone https://github.com/yrvy/reblex.git
cd reblex
pip install -e .
```

## Usage

### Command Line

```bash
# Show installation info
python main.py --info

# Launch from a protocol URL
python main.py "roblox-player:1+launchmode:play+gameinfo:TOKEN..."

# Launch a specific place
python main.py --place 123456789

# Register as protocol handler
python main.py --register

# Unregister protocol handler
python main.py --unregister
```

### As a Library

```python
from roblox_launcher import RobloxLauncher, parse_roblox_url

# Create launcher
launcher = RobloxLauncher()

# Check if Roblox is available
if launcher.is_available:
    print(f"Roblox found at: {launcher.player_path}")

# Launch from URL
result = launcher.launch_url("roblox-player:1+launchmode:play+...")
if result.success:
    print("Launched!")

# Launch a specific place
result = launcher.launch_place("123456789")

# Parse URL parameters
params = parse_roblox_url("roblox-player:1+launchmode:play+placeid:123")
print(f"Place ID: {params.place_id}")
print(f"Launch mode: {params.launch_mode}")
```

## Project Structure

```
reblex/
├── main.py                  # CLI entry point
├── roblox_launcher/
│   ├── __init__.py          # Package exports
│   ├── launcher.py          # Main launcher classes
│   ├── protocol.py          # URL parsing
│   ├── finder.py            # Roblox installation detection
│   └── register.py          # Protocol handler registration
├── pyproject.toml           # Package configuration
└── README.md
```

## How It Works

1. **URL Parsing**: Parses `roblox-player://` URLs into structured parameters
2. **Roblox Detection**: Finds the Roblox installation in `%LOCALAPPDATA%\Roblox\Versions`
3. **Process Launch**: Spawns `RobloxPlayerBeta.exe` with the appropriate command-line arguments

## License

MIT
