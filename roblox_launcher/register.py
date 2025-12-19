"""
Protocol handler registration for Windows.

Allows registering this launcher as the handler for roblox-player:// URLs.
"""

import sys
import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def _get_python_executable() -> str:
    """Get the path to the current Python executable."""
    return sys.executable


def _get_script_path() -> str:
    """Get the path to the main launcher script."""
    # This should be adjusted based on how the launcher is installed
    return str(Path(__file__).parent.parent / "main.py")


def register_protocol_handler(
    handler_path: Optional[str] = None,
    protocol: str = "roblox-player"
) -> bool:
    """
    Register this launcher as the protocol handler for roblox-player:// URLs.

    This requires administrator privileges on Windows.

    Args:
        handler_path: Path to the handler executable/script.
                     If None, uses the current script.
        protocol: The protocol to register (default: roblox-player)

    Returns:
        True if registration succeeded, False otherwise.
    """
    if sys.platform != "win32":
        logger.error("Protocol handler registration is only supported on Windows")
        return False

    try:
        import winreg
    except ImportError:
        logger.error("winreg module not available")
        return False

    if handler_path is None:
        python_exe = _get_python_executable()
        script_path = _get_script_path()
        handler_path = f'"{python_exe}" "{script_path}" "%1"'

    try:
        # Create the protocol key
        key_path = f"SOFTWARE\\Classes\\{protocol}"

        # Create main protocol key
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f"URL:{protocol} Protocol")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")

        # Create shell\open\command key
        command_key_path = f"{key_path}\\shell\\open\\command"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, command_key_path) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, handler_path)

        logger.info(f"Successfully registered {protocol}:// protocol handler")
        return True

    except PermissionError:
        logger.error("Permission denied. Try running as administrator.")
        return False
    except Exception as e:
        logger.error(f"Failed to register protocol handler: {e}")
        return False


def unregister_protocol_handler(protocol: str = "roblox-player") -> bool:
    """
    Unregister the protocol handler.

    Args:
        protocol: The protocol to unregister

    Returns:
        True if unregistration succeeded, False otherwise.
    """
    if sys.platform != "win32":
        logger.error("Protocol handler unregistration is only supported on Windows")
        return False

    try:
        import winreg
    except ImportError:
        logger.error("winreg module not available")
        return False

    try:
        key_path = f"SOFTWARE\\Classes\\{protocol}"

        # Delete the key tree
        def delete_key_tree(root, path):
            try:
                with winreg.OpenKey(root, path, 0, winreg.KEY_ALL_ACCESS) as key:
                    while True:
                        try:
                            subkey = winreg.EnumKey(key, 0)
                            delete_key_tree(root, f"{path}\\{subkey}")
                        except OSError:
                            break
                winreg.DeleteKey(root, path)
            except FileNotFoundError:
                pass

        delete_key_tree(winreg.HKEY_CURRENT_USER, key_path)

        logger.info(f"Successfully unregistered {protocol}:// protocol handler")
        return True

    except PermissionError:
        logger.error("Permission denied. Try running as administrator.")
        return False
    except Exception as e:
        logger.error(f"Failed to unregister protocol handler: {e}")
        return False


def is_protocol_registered(protocol: str = "roblox-player") -> bool:
    """
    Check if the protocol is registered.

    Args:
        protocol: The protocol to check

    Returns:
        True if registered, False otherwise.
    """
    if sys.platform != "win32":
        return False

    try:
        import winreg
    except ImportError:
        return False

    try:
        key_path = f"SOFTWARE\\Classes\\{protocol}"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path):
            return True
    except FileNotFoundError:
        pass

    # Also check HKEY_CLASSES_ROOT (system-wide)
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, protocol):
            return True
    except FileNotFoundError:
        pass

    return False


def get_registered_handler(protocol: str = "roblox-player") -> Optional[str]:
    """
    Get the currently registered handler for the protocol.

    Args:
        protocol: The protocol to check

    Returns:
        The handler command string, or None if not registered.
    """
    if sys.platform != "win32":
        return None

    try:
        import winreg
    except ImportError:
        return None

    # Check user registry first
    try:
        key_path = f"SOFTWARE\\Classes\\{protocol}\\shell\\open\\command"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            value, _ = winreg.QueryValueEx(key, "")
            return value
    except FileNotFoundError:
        pass

    # Check system registry
    try:
        key_path = f"{protocol}\\shell\\open\\command"
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
            value, _ = winreg.QueryValueEx(key, "")
            return value
    except FileNotFoundError:
        pass

    return None
