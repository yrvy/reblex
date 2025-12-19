import { useState, useEffect } from 'react';
import { waitForApi, getCurrentUser, isLoggedIn } from './api';
import type { User } from './types';
import LoginPage from './pages/LoginPage';
import HomePage from './pages/HomePage';

function App() {
  const [ready, setReady] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function init() {
      // Wait for pywebview API
      await waitForApi();
      setReady(true);

      // Check if already logged in
      const loggedIn = await isLoggedIn();
      if (loggedIn) {
        const currentUser = await getCurrentUser();
        setUser(currentUser);
      }
      setLoading(false);
    }

    init();
  }, []);

  if (!ready || loading) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="text-dark-400 text-lg">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage onLogin={setUser} />;
  }

  return <HomePage user={user} onLogout={() => setUser(null)} />;
}

export default App;
