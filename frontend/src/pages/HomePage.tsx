import { useState } from 'react';
import type { User, GameInfo, GameServer } from '../types';
import { logout, getGameInfo, getServers, launchGame } from '../api';

interface HomePageProps {
  user: User;
  onLogout: () => void;
}

export default function HomePage({ user, onLogout }: HomePageProps) {
  const [placeId, setPlaceId] = useState('');
  const [game, setGame] = useState<GameInfo | null>(null);
  const [servers, setServers] = useState<GameServer[]>([]);
  const [loading, setLoading] = useState(false);
  const [launching, setLaunching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const id = parseInt(placeId);
    if (isNaN(id)) {
      setError('Please enter a valid Place ID');
      return;
    }

    setError(null);
    setMessage(null);
    setLoading(true);
    setGame(null);
    setServers([]);

    try {
      const gameInfo = await getGameInfo(id);
      if (gameInfo) {
        setGame(gameInfo);
        const serverList = await getServers(id, 10);
        setServers(serverList);
      } else {
        setError('Game not found');
      }
    } catch {
      setError('Failed to fetch game info');
    } finally {
      setLoading(false);
    }
  };

  const handleLaunch = async (jobId?: string) => {
    if (!game) return;

    setLaunching(true);
    setError(null);
    setMessage(null);

    try {
      const result = await launchGame(game.placeId, jobId);
      if (result.success) {
        setMessage(result.message);
      } else {
        setError(result.message);
      }
    } catch {
      setError('Failed to launch game');
    } finally {
      setLaunching(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    onLogout();
  };

  const formatNumber = (n: number) => {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
    return n.toString();
  };

  return (
    <div className="min-h-screen bg-dark-950">
      {/* Header */}
      <header className="bg-dark-900 border-b border-dark-700 px-6 py-4">
        <div className="flex items-center justify-between max-w-6xl mx-auto">
          <h1 className="text-xl font-bold text-white">Reblex</h1>

          <div className="flex items-center gap-4">
            <span className="text-dark-300">
              {user.displayName}
              <span className="text-dark-500 ml-1">@{user.username}</span>
            </span>
            <button
              onClick={handleLogout}
              className="text-dark-400 hover:text-white transition-colors text-sm"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto p-6">
        {/* Search Form */}
        <form onSubmit={handleSearch} className="mb-8">
          <div className="flex gap-3">
            <input
              type="text"
              value={placeId}
              onChange={(e) => setPlaceId(e.target.value)}
              placeholder="Enter Place ID..."
              className="flex-1 bg-dark-800 text-white rounded-lg px-4 py-3
                       border border-dark-600 focus:border-blue-500 focus:outline-none"
            />
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/50
                       text-white font-medium py-3 px-6 rounded-lg transition-colors"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </form>

        {/* Messages */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {message && (
          <div className="mb-6 p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
            <p className="text-green-400">{message}</p>
          </div>
        )}

        {/* Game Info */}
        {game && (
          <div className="animate-fadeIn">
            <div className="bg-dark-900 rounded-xl p-6 border border-dark-700 mb-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-1">{game.name}</h2>
                  <p className="text-dark-400">
                    by {game.creatorName} • {game.genre}
                  </p>
                </div>
                <button
                  onClick={() => handleLaunch()}
                  disabled={launching}
                  className="bg-green-600 hover:bg-green-700 disabled:bg-green-600/50
                           text-white font-medium py-2 px-6 rounded-lg transition-colors"
                >
                  {launching ? 'Launching...' : 'Play'}
                </button>
              </div>

              <p className="text-dark-300 text-sm mb-4 line-clamp-2">
                {game.description || 'No description'}
              </p>

              <div className="flex gap-6 text-sm">
                <div>
                  <span className="text-dark-500">Playing</span>
                  <p className="text-white font-medium">{formatNumber(game.playing)}</p>
                </div>
                <div>
                  <span className="text-dark-500">Visits</span>
                  <p className="text-white font-medium">{formatNumber(game.visits)}</p>
                </div>
                <div>
                  <span className="text-dark-500">Favorites</span>
                  <p className="text-white font-medium">{formatNumber(game.favorites)}</p>
                </div>
                <div>
                  <span className="text-dark-500">Max Players</span>
                  <p className="text-white font-medium">{game.maxPlayers}</p>
                </div>
              </div>
            </div>

            {/* Servers */}
            {servers.length > 0 && (
              <div className="bg-dark-900 rounded-xl border border-dark-700">
                <div className="px-6 py-4 border-b border-dark-700">
                  <h3 className="text-lg font-semibold text-white">Servers</h3>
                </div>
                <div className="divide-y divide-dark-700">
                  {servers.map((server, i) => (
                    <div
                      key={server.jobId}
                      className="px-6 py-4 flex items-center justify-between hover:bg-dark-800/50"
                    >
                      <div className="flex items-center gap-4">
                        <span className="text-dark-500 w-8">#{i + 1}</span>
                        <div>
                          <p className="text-white font-medium">
                            {server.playing} / {server.maxPlayers} players
                          </p>
                          <p className="text-dark-500 text-xs font-mono">
                            {server.jobId.slice(0, 20)}...
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => handleLaunch(server.jobId)}
                        disabled={launching}
                        className="bg-dark-700 hover:bg-dark-600 disabled:bg-dark-700/50
                                 text-white py-2 px-4 rounded-lg transition-colors text-sm"
                      >
                        Join
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!game && !loading && (
          <div className="text-center py-16">
            <div className="text-dark-600 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <h3 className="text-dark-400 text-lg mb-2">Search for a game</h3>
            <p className="text-dark-500">Enter a Place ID to view game info and servers</p>
          </div>
        )}
      </main>
    </div>
  );
}
