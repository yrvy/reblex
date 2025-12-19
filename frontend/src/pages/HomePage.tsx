import { useState, useEffect } from 'react';
import type { User, Friend, HomeGame, HomeFeed } from '../types';
import { logout, getHomeFeed, launchGame, searchGames } from '../api';

interface HomePageProps {
  user: User;
  onLogout: () => void;
}

// Friend card component
function FriendCard({ friend, onJoin }: { friend: Friend; onJoin: (placeId: number, jobId?: string) => void }) {
  const statusColors = {
    ingame: 'bg-green-500',
    studio: 'bg-orange-500',
    online: 'bg-blue-500',
    offline: 'bg-gray-500',
  };

  return (
    <div
      className="flex flex-col items-center gap-1 cursor-pointer hover:opacity-80 transition-opacity"
      onClick={() => friend.placeId && onJoin(friend.placeId, friend.jobId)}
      title={friend.gameName || friend.displayName}
    >
      <div className="relative">
        <img
          src={friend.avatar || '/placeholder-avatar.png'}
          alt={friend.displayName}
          className="w-16 h-16 rounded-full bg-dark-700 object-cover"
        />
        <div className={`absolute bottom-0 right-0 w-4 h-4 rounded-full border-2 border-dark-900 ${statusColors[friend.status]}`} />
      </div>
      <span className="text-xs text-white font-medium truncate w-16 text-center">{friend.displayName}</span>
      {friend.gameName && (
        <span className="text-[10px] text-dark-400 truncate w-16 text-center">{friend.gameName}</span>
      )}
    </div>
  );
}

// Game card component
function GameCard({ game, onPlay }: { game: HomeGame; onPlay: (placeId: number) => void }) {
  const rating = game.upvotes + game.downvotes > 0
    ? Math.round((game.upvotes / (game.upvotes + game.downvotes)) * 100)
    : 0;

  const formatCount = (n: number) => {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
    return n.toString();
  };

  return (
    <div
      className="group cursor-pointer"
      onClick={() => onPlay(game.placeId)}
    >
      <div className="relative rounded-lg overflow-hidden bg-dark-800 aspect-video mb-2">
        {game.thumbnail ? (
          <img
            src={game.thumbnail}
            alt={game.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
          />
        ) : (
          <div className="w-full h-full bg-dark-700 flex items-center justify-center">
            <span className="text-dark-500">No image</span>
          </div>
        )}
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
          <div className="opacity-0 group-hover:opacity-100 transition-opacity">
            <div className="bg-green-600 px-4 py-2 rounded-lg font-medium text-white">
              Play
            </div>
          </div>
        </div>
      </div>
      <h3 className="text-white font-medium truncate group-hover:text-blue-400 transition-colors">
        {game.name}
      </h3>
      <div className="flex items-center gap-3 text-xs text-dark-400">
        {rating > 0 && (
          <span className="flex items-center gap-1">
            <span className="text-green-400">👍</span> {rating}%
          </span>
        )}
        <span className="flex items-center gap-1">
          <span>👥</span> {formatCount(game.playerCount)}
        </span>
      </div>
    </div>
  );
}

export default function HomePage({ user, onLogout }: HomePageProps) {
  const [feed, setFeed] = useState<HomeFeed | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<HomeGame[]>([]);
  const [launching, setLaunching] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadFeed();
  }, []);

  const loadFeed = async () => {
    setLoading(true);
    try {
      const data = await getHomeFeed();
      setFeed(data);
    } catch (err) {
      console.error('Failed to load feed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    try {
      const results = await searchGames(searchQuery);
      setSearchResults(results);
    } catch {
      // ignore
    }
  };

  const handlePlay = async (placeId: number, jobId?: string) => {
    setLaunching(true);
    setMessage(null);
    try {
      const result = await launchGame(placeId, jobId);
      setMessage({
        type: result.success ? 'success' : 'error',
        text: result.message,
      });
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to launch game' });
    } finally {
      setLaunching(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    onLogout();
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-dark-900 to-dark-950">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-dark-900/95 backdrop-blur border-b border-dark-700">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <h1 className="text-xl font-bold text-white">Reblex</h1>
            <nav className="flex gap-1">
              <button className="px-4 py-2 rounded-lg bg-dark-700 text-white text-sm font-medium">
                Home
              </button>
              <button className="px-4 py-2 rounded-lg text-dark-400 hover:text-white text-sm font-medium transition-colors">
                Friends
              </button>
            </nav>
          </div>

          <div className="flex items-center gap-4">
            {/* Search */}
            <form onSubmit={handleSearch} className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search games..."
                className="w-64 bg-dark-800 text-white rounded-lg px-4 py-2 pl-10 text-sm
                         border border-dark-600 focus:border-blue-500 focus:outline-none"
              />
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </form>

            {/* User */}
            <div className="flex items-center gap-3">
              <span className="text-dark-300 text-sm">{user.displayName}</span>
              <img
                src={user.avatar || '/placeholder-avatar.png'}
                alt={user.displayName}
                className="w-8 h-8 rounded-full bg-dark-700"
              />
              <button
                onClick={handleLogout}
                className="text-dark-400 hover:text-white transition-colors text-sm"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Messages */}
      {message && (
        <div className={`fixed top-20 right-6 z-50 px-4 py-3 rounded-lg shadow-lg animate-slideUp ${
          message.type === 'success' ? 'bg-green-500/20 border border-green-500/50 text-green-400' : 'bg-red-500/20 border border-red-500/50 text-red-400'
        }`}>
          {message.text}
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        {loading ? (
          <div className="text-center py-20">
            <div className="text-dark-400">Loading...</div>
          </div>
        ) : (
          <>
            {/* Search Results */}
            {searchResults.length > 0 && (
              <section className="mb-8 animate-fadeIn">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-white">Search Results</h2>
                  <button
                    onClick={() => setSearchResults([])}
                    className="text-dark-400 hover:text-white text-sm"
                  >
                    Clear
                  </button>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                  {searchResults.map((game) => (
                    <GameCard key={game.universeId} game={game} onPlay={handlePlay} />
                  ))}
                </div>
              </section>
            )}

            {/* Friends */}
            {feed?.friends && feed.friends.length > 0 && (
              <section className="mb-8">
                <h2 className="text-lg font-semibold text-white mb-4">Friends</h2>
                <div className="flex gap-4 overflow-x-auto pb-2">
                  {feed.friends.map((friend) => (
                    <FriendCard key={friend.id} friend={friend} onJoin={handlePlay} />
                  ))}
                </div>
              </section>
            )}

            {/* Continue Playing */}
            {feed?.continue && feed.continue.length > 0 && (
              <section className="mb-8">
                <h2 className="text-xl font-semibold text-white mb-4">Jump back in!</h2>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                  {feed.continue.map((game) => (
                    <GameCard key={game.universeId} game={game} onPlay={handlePlay} />
                  ))}
                </div>
              </section>
            )}

            {/* Favorites */}
            {feed?.favorites && feed.favorites.length > 0 && (
              <section className="mb-8">
                <h2 className="text-xl font-semibold text-white mb-4">Favorites</h2>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                  {feed.favorites.map((game) => (
                    <GameCard key={game.universeId} game={game} onPlay={handlePlay} />
                  ))}
                </div>
              </section>
            )}

            {/* Empty State */}
            {!feed?.friends?.length && !feed?.continue?.length && !feed?.favorites?.length && (
              <div className="text-center py-20">
                <div className="text-dark-600 mb-4">
                  <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                      d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                      d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-dark-400 text-lg mb-2">No games yet</h3>
                <p className="text-dark-500">Search for games to get started</p>
              </div>
            )}
          </>
        )}
      </main>

      {/* Launching Overlay */}
      {launching && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-dark-900 rounded-xl p-6 text-center">
            <div className="animate-spin w-8 h-8 border-2 border-white border-t-transparent rounded-full mx-auto mb-4" />
            <p className="text-white">Launching game...</p>
          </div>
        </div>
      )}
    </div>
  );
}
