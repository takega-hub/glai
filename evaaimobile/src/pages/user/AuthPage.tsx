import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Lock, Mail, Sparkles } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { login, register, loginAsGuest } from '../../api/userApiClient';

const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const setAuth = useAuthStore((state) => state.setAuth);
  const navigate = useNavigate();

  const handleEmailAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = isLogin 
        ? await login({ email, password }) 
        : await register({ email, password, username: name });
      if (response.data.access_token && response.data.user) {
        setAuth(response.data.access_token, response.data.user);
        navigate('/user');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleGuestAuth = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await loginAsGuest();
      if (response.data.access_token && response.data.user) {
        setAuth(response.data.access_token, response.data.user);
        navigate('/user');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to log in as guest');
    } finally {
      setLoading(false);
    }
  };

  const toggleAuthMode = () => {
    setIsLogin(!isLogin);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-white/10 shadow-xl shadow-purple-500/10">
          <div className="text-center mb-8">
            <div className="inline-block p-3 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl mb-4">
              <Sparkles className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-purple-300 bg-clip-text text-transparent">
              Sign in or create an account
            </h1>
            <p className="text-purple-300 mt-2 text-sm">
              By continuing, you agree to our <a href="#" className="underline hover:text-white">Terms of Use</a> and <a href="#" className="underline hover:text-white">Privacy Policy</a>
            </p>
          </div>

          <div className="space-y-4 mb-6">
            <button className="w-full flex items-center justify-center space-x-3 bg-black/30 text-white py-3 px-4 rounded-xl hover:bg-black/50 transition-all duration-300 border border-white/20">
              <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor"><path d="M12.15,2.5a9.65,9.65,0,0,0-7,11.87,9.43,9.43,0,0,0,4.29,4.78,1,1,0,0,0,1.21-.19,1,1,0,0,0-.19-1.21,7.5,7.5,0,0,1-3.23-4,7.62,7.62,0,0,1,6.86-8.3,7.49,7.49,0,0,1,8,6.85,1,1,0,0,0,1,.88,1,1,0,0,0,1-1.09,9.6,9.6,0,0,0-10.7-8.7Zm.29,8.37a1,1,0,0,0-1.41,0,1,1,0,0,0,0,1.41,3.42,3.42,0,0,0,1.41,1,1,1,0,0,0,0-1.41,1.4,1.4,0,0,0-1-1Zm-2.6,3.18a1,1,0,0,0-1.41,0,1,1,0,0,0,0,1.41,3.42,3.42,0,0,0,1.41,1,1,1,0,0,0,0-1.41,1.4,1.4,0,0,0-1-1Zm5.2,0a1,1,0,0,0-1.41,0,1,1,0,0,0,0,1.41,3.42,3.42,0,0,0,1.41,1,1,1,0,0,0,0-1.41,1.4,1.4,0,0,0-1-1Zm-2.6-3.18a1,1,0,0,0-1.41,0,1,1,0,0,0,0,1.41,3.42,3.42,0,0,0,1.41,1,1,1,0,0,0,0-1.41,1.4,1.4,0,0,0-1-1Z"/></svg>
              <span>Continue with Apple ID</span>
            </button>
            <button className="w-full flex items-center justify-center space-x-3 bg-white/90 text-slate-800 py-3 px-4 rounded-xl hover:bg-white transition-all duration-300 font-semibold">
              <svg className="w-5 h-5" viewBox="0 0 48 48"><path fill="#FFC107" d="M43.611,20.083H42V20H24v8h11.303c-1.649,4.657-6.08,8-11.303,8c-6.627,0-12-5.373-12-12c0-6.627,5.373-12,12-12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C12.955,4,4,12.955,4,24c0,11.045,8.955,20,20,20c11.045,0,20-8.955,20-20C44,22.659,43.862,21.35,43.611,20.083z"/><path fill="#FF3D00" d="M6.306,14.691l6.571,4.819C14.655,15.108,18.961,12,24,12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C16.318,4,9.656,8.337,6.306,14.691z"/><path fill="#4CAF50" d="M24,44c5.166,0,9.86-1.977,13.409-5.192l-6.19-5.238C29.211,35.091,26.715,36,24,36c-5.222,0-9.619-3.317-11.283-7.946l-6.522,5.025C9.505,39.556,16.227,44,24,44z"/><path fill="#1976D2" d="M43.611,20.083H42V20H24v8h11.303c-0.792,2.237-2.231,4.166-4.087,5.571l6.19,5.238C39.901,36.626,44,30.638,44,24C44,22.659,43.862,21.35,43.611,20.083z"/></svg>
              <span>Continue with Google</span>
            </button>
          </div>

          <div className="flex items-center justify-center space-x-4 my-6">
            <span className="h-px w-full bg-white/20"></span>
            <span className="text-purple-300 text-sm">or</span>
            <span className="h-px w-full bg-white/20"></span>
          </div>

          {error && (
            <div className="bg-red-500/20 text-red-300 border border-red-500/30 rounded-xl p-3 text-center text-sm mb-6">
              {error}
            </div>
          )}

          <form className="space-y-6" onSubmit={handleEmailAuth}>
            {!isLogin && (
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-purple-300" />
                <input
                  type="text"
                  placeholder="Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="w-full bg-white/10 border border-white/20 rounded-xl py-3 pl-12 pr-4 text-white placeholder-purple-300/70 focus:outline-none focus:ring-2 focus:ring-purple-400 transition-all"
                />
              </div>
            )}
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-purple-300" />
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-white/10 border border-white/20 rounded-xl py-3 pl-12 pr-4 text-white placeholder-purple-300/70 focus:outline-none focus:ring-2 focus:ring-purple-400 transition-all"
              />
            </div>

            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-purple-300" />
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full bg-white/10 border border-white/20 rounded-xl py-3 pl-12 pr-4 text-white placeholder-purple-300/70 focus:outline-none focus:ring-2 focus:ring-purple-400 transition-all"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-white/20 text-white py-3 px-4 rounded-xl hover:bg-white/30 transition-all duration-300 font-semibold border border-white/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (isLogin ? 'Signing in...' : 'Creating account...') : (isLogin ? 'Continue with Email' : 'Create account')}
            </button>
          </form>

          <div className="text-center mt-8">
            <button 
              onClick={handleGuestAuth} 
              disabled={loading}
              className="font-semibold text-purple-200 hover:text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Log in as guest
            </button>
          </div>

          <div className="text-center mt-4">
            <p className="text-purple-300 text-sm">
              {isLogin ? "Don't have an account?" : 'Already have an account?'}{' '}
              <button onClick={toggleAuthMode} className="font-semibold text-purple-200 hover:text-white transition-all">
                {isLogin ? 'Sign up' : 'Sign in'}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;