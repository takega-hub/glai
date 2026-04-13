import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Home, User, Menu, X, Sparkles, LogOut, Heart } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { useThemeStore } from '../../store/themeStore';

declare global {
    interface Window {
        Telegram: any;
    }
}

const UserLayout = () => {
  const { theme } = useThemeStore();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const logout = useAuthStore((state) => state.logout);

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(theme);

    if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.ready();
        window.Telegram.WebApp.expand();
    }
  }, [theme]);

  const handleLogout = () => {
    logout();
    navigate('/auth');
  };

  const isActive = (path: string) => {
    if (path === '') return location.pathname === '/user' || location.pathname === '/user/';
    return location.pathname.startsWith(`/user/${path}`);
  };

  const navigation = [
    { name: 'Chats', href: '', icon: Home },
    { name: 'Profile', href: 'profile', icon: User },
    { name: 'Favorites', href: 'favorites', icon: Heart },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex flex-col">
      {/* Header */}
      <header className="bg-white/5 backdrop-blur-md border-b border-white/10 sticky top-0 z-50 flex-shrink-0">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3 flex-shrink-0">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-white to-purple-300 bg-clip-text text-transparent">
                GL AI
              </h1>
            </div>
            
            {/* Desktop Navigation - Fixed jumping issue */}
            <nav className="hidden md:flex space-x-1">
              {navigation.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`
                      flex items-center space-x-2 px-4 py-2 rounded-xl transition-all duration-300
                      ${active 
                        ? 'bg-white/10 text-white shadow-sm' 
                        : 'text-purple-300 hover:text-white hover:bg-white/10'
                      }
                    `}
                    style={{
                      // Fix for border jumping - using box-shadow instead of border
                      boxShadow: active ? '0 0 0 1px rgba(168, 85, 247, 0.3)' : 'none'
                    }}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="font-medium">{item.name}</span>
                  </Link>
                );
              })}
            </nav>

            <div className="hidden md:flex items-center flex-shrink-0">
              <button
                onClick={handleLogout}
                className="flex items-center space-x-2 px-4 py-2 rounded-xl text-purple-300 hover:text-white hover:bg-white/10 transition-all duration-300"
              >
                <LogOut className="w-5 h-5" />
                <span className="font-medium">Logout</span>
              </button>
            </div>

            {/* Mobile menu button */}
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="md:hidden text-white p-2 rounded-lg hover:bg-white/10 transition-all flex-shrink-0"
            >
              {isMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
          </div>

          {/* Mobile Navigation */}
          {isMenuOpen && (
            <div className="md:hidden border-t border-white/10 mt-2 pb-2">
              <div className="px-2 pt-2 space-y-1">
                {navigation.map((item) => {
                  const Icon = item.icon;
                  const active = isActive(item.href);
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={`
                        flex items-center space-x-3 px-3 py-3 rounded-xl transition-all
                        ${active 
                          ? 'bg-white/10 text-white' 
                          : 'text-purple-300 hover:text-white hover:bg-white/10'
                        }
                      `}
                      onClick={() => setIsMenuOpen(false)}
                    >
                      <Icon className="w-5 h-5" />
                      <span className="font-medium">{item.name}</span>
                    </Link>
                  );
                })}
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-3 px-3 py-3 rounded-xl text-purple-300 hover:text-white hover:bg-white/10 transition-all w-full"
                >
                  <LogOut className="w-5 h-5" />
                  <span className="font-medium">Logout</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white/5 border-t border-white/10 flex-shrink-0">
        <div className="px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-purple-300 text-opacity-80 text-sm">
            © 2026 GL AI. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default UserLayout;