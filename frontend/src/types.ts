// Types for the Python API bridge

export interface User {
  id: number;
  username: string;
  displayName: string;
  avatar?: string;
}

export interface Friend {
  id: number;
  username: string;
  displayName: string;
  avatar?: string;
  status: 'offline' | 'online' | 'ingame' | 'studio';
  gameName?: string;
  placeId?: number;
  jobId?: string;
}

export interface HomeGame {
  universeId: number;
  placeId: number;
  name: string;
  playerCount: number;
  upvotes: number;
  downvotes: number;
  thumbnail?: string;
  icon?: string;
}

export interface HomeFeed {
  friends: Friend[];
  continue: HomeGame[];
  favorites: HomeGame[];
  error?: string;
}

export interface GameInfo {
  universeId: number;
  placeId: number;
  name: string;
  description: string;
  creatorName: string;
  creatorType: string;
  playing: number;
  visits: number;
  maxPlayers: number;
  favorites: number;
  genre: string;
}

export interface GameServer {
  jobId: string;
  playing: number;
  maxPlayers: number;
  ping: number;
  fps: number;
}

export interface LoginResult {
  success: boolean;
  user: User | null;
  error: string | null;
}

export interface LaunchResult {
  success: boolean;
  message: string;
}

// PyWebview API interface
export interface PyWebviewApi {
  // Auth
  is_logged_in(): Promise<boolean>;
  login(cookie: string): Promise<LoginResult>;
  logout(): Promise<void>;
  get_current_user(): Promise<User | null>;

  // Home Feed
  get_home_feed(): Promise<HomeFeed>;
  get_friends(limit?: number): Promise<Friend[]>;
  search_games(query: string): Promise<HomeGame[]>;

  // Games
  get_game_info(placeId: number): Promise<GameInfo | null>;
  get_servers(placeId: number, limit?: number): Promise<GameServer[]>;
  launch_game(placeId: number, jobId?: string | null): Promise<LaunchResult>;

  // Utility
  is_roblox_installed(): Promise<boolean>;
}

// Extend window type
declare global {
  interface Window {
    pywebview?: {
      api: PyWebviewApi;
    };
  }
}
