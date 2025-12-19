import type { PyWebviewApi, User, GameInfo, GameServer, LoginResult, LaunchResult } from './types';

/**
 * Wait for pywebview API to be ready
 */
export function waitForApi(): Promise<PyWebviewApi> {
  return new Promise((resolve) => {
    if (window.pywebview?.api) {
      resolve(window.pywebview.api);
      return;
    }

    // Poll for API availability
    const interval = setInterval(() => {
      if (window.pywebview?.api) {
        clearInterval(interval);
        resolve(window.pywebview.api);
      }
    }, 50);
  });
}

/**
 * Get the pywebview API (throws if not ready)
 */
export function getApi(): PyWebviewApi {
  if (!window.pywebview?.api) {
    throw new Error('PyWebview API not ready');
  }
  return window.pywebview.api;
}

// Convenience wrapper functions

export async function isLoggedIn(): Promise<boolean> {
  const api = await waitForApi();
  return api.is_logged_in();
}

export async function login(cookie: string): Promise<LoginResult> {
  const api = await waitForApi();
  return api.login(cookie);
}

export async function logout(): Promise<void> {
  const api = await waitForApi();
  return api.logout();
}

export async function getCurrentUser(): Promise<User | null> {
  const api = await waitForApi();
  return api.get_current_user();
}

export async function getGameInfo(placeId: number): Promise<GameInfo | null> {
  const api = await waitForApi();
  return api.get_game_info(placeId);
}

export async function getServers(placeId: number, limit: number = 10): Promise<GameServer[]> {
  const api = await waitForApi();
  return api.get_servers(placeId, limit);
}

export async function launchGame(placeId: number, jobId?: string | null): Promise<LaunchResult> {
  const api = await waitForApi();
  return api.launch_game(placeId, jobId ?? null);
}

export async function isRobloxInstalled(): Promise<boolean> {
  const api = await waitForApi();
  return api.is_roblox_installed();
}
