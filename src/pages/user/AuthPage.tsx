import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Lock, Mail, Sparkles } from 'lucide-react';
import { GoogleLogin, CredentialResponse } from '@react-oauth/google';
import { webAuthService } from '../../services/webAuthService';
import { useAuthStore } from '../../store/authStore';

// Apple Sign-In is not available in browsers outside of Safari.
// We will use a placeholder for now.
const AppleSignInButton = ({ onClick }: { onClick: () => void }) => (
  <button 
    onClick={onClick}
    className="w-full flex items-center justify-center space-x-3 bg-black/30 text-white py-3 px-4 rounded-xl hover:bg-black/50 transition-all duration-300 border border-white/20">
    <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor"><path d="M12.15,2.5a9.65,9.65,0,0,0-7,11.87,9.43,9.43,0,0,0,4.29,4.78,1,1,0,0,0,1.21-.19,1,1,0,0,0-.19-1.21,7.5,7.5,0,0,1-3.23-4,7.62,7.62,0,0,1,6.86-8.3,7.49,7.49,0,0,1,8,6.85,1,1,0,0,0,1,.88,1,1,0,0,0,1-1.09,9.6,9.6,0,0,0-10.7-8.7Zm.29,8.37a1,1,0,0,0-1.41,0,1,1,0,0,0,0,1.41,3.42,3.42,0,0,0,1.41,1,1,1,0,0,0,0-1.41,1.4,1.4,0,0,0-1-1Zm-2.6,3.18a1,1,0,0,0-1.41,0,1,1,0,0,0,0,1.41,3.42,3.42,0,0,0,1.41,1,1,1,0,0,0,0-1.41,1.4,1.4,0,0,0-1-1Zm5.2,0a1,1,0,0,0-1.41,0,1,1,0,0,0,0,1.41,3.42,3.42,0,0,0,1.41,1,1,1,0,0,0,0-1.41,1.4,1.4,0,0,0-1-1Zm-2.6-3.18a1,1,0,0,0-1.41,0,1,1,0,0,0,0,1.41,3.42,3.42,0,0,0,1.41,1,1,1,0,0,0,0-1.41,1.4,1.4,0,0,0-1-1Z"/></svg>
    <span>Continue with Apple ID</span>
  </button>
);

const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleGoogleSuccess = async (credentialResponse: CredentialResponse) => {
    if (credentialResponse.credential) {
        setLoading(true);
        setError(null);
        try {
            await webAuthService.loginWithGoogle(credentialResponse.credential);
            navigate('/user');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Google Sign-In failed');
        } finally {
            setLoading(false);
        }
    } else {
        setError('Google Sign-In failed: No credential received');
    }
  };

  const handleAppleLogin = async () => {
    try {
      const data = await AppleID.auth.signIn();
      const { authorization, user } = data;

      if (authorization && authorization.id_token) {
        setLoading(true);
        setError(null);

        const fullName = user ? `${user.name.firstName} ${user.name.lastName}` : null;
        const email = user ? user.email : null;

        try {
          await webAuthService.loginWithApple(authorization.id_token, fullName, email);
          navigate('/user');
        } catch (err: any) {
          setError(err.response?.data?.detail || 'Apple Sign-In failed on backend');
        } finally {
          setLoading(false);
        }
      } else {
        setError('Apple Sign-In failed: No authorization token received.');
      }
    } catch (error) {
      setError('Apple Sign-In was canceled or failed.');
      console.error(error);
    }
  };

  const handleEmailAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (isLogin) {
        await webAuthService.login(email, password);
      } else {
        await webAuthService.register(email, password, name);
      }
      navigate('/user');
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
          await webAuthService.loginAsGuest();
          navigate('/user');
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
            <AppleSignInButton onClick={handleAppleLogin} />
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={() => {
                setError('Google Sign-In was canceled or failed');
              }}
              theme="outline"
              size="large"
              shape="pill"
              width="100%"
            />
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
                  required={!isLogin}
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