import { useState } from 'react';
import { login } from '../api';
import type { User } from '../types';

interface LoginPageProps {
  onLogin: (user: User) => void;
}

export default function LoginPage({ onLogin }: LoginPageProps) {
  const [cookie, setCookie] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cookie.trim()) {
      setError('Please enter your cookie');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const result = await login(cookie);
      if (result.success && result.user) {
        onLogin(result.user);
      } else {
        setError(result.error || 'Login failed');
      }
    } catch (err) {
      setError('Failed to connect to Roblox');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md animate-slideUp">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Reblex</h1>
          <p className="text-dark-400">Roblox Launcher</p>
        </div>

        {/* Login Form */}
        <div className="bg-dark-900 rounded-xl p-6 shadow-xl border border-dark-700">
          <h2 className="text-xl font-semibold text-white mb-4">Login</h2>

          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-dark-300 text-sm mb-2">
                .ROBLOSECURITY Cookie
              </label>
              <textarea
                value={cookie}
                onChange={(e) => setCookie(e.target.value)}
                placeholder="Paste your cookie here..."
                className="w-full bg-dark-800 text-white rounded-lg px-4 py-3
                         border border-dark-600 focus:border-blue-500 focus:outline-none
                         resize-none h-32 text-sm font-mono"
                disabled={loading}
              />
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/50
                       text-white font-medium py-3 px-4 rounded-lg transition-colors
                       flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12" cy="12" r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  Logging in...
                </>
              ) : (
                'Login'
              )}
            </button>
          </form>

          <div className="mt-4 pt-4 border-t border-dark-700">
            <p className="text-dark-500 text-xs text-center">
              Your cookie is stored locally and never sent anywhere except Roblox.
            </p>
          </div>
        </div>

        {/* Help */}
        <div className="mt-6 text-center">
          <p className="text-dark-500 text-sm">
            Need help getting your cookie?{' '}
            <a
              href="#"
              className="text-blue-400 hover:text-blue-300"
              onClick={(e) => {
                e.preventDefault();
                // Could open a help modal here
              }}
            >
              View guide
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
