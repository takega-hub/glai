import { Routes, Route, Navigate } from 'react-router-dom';
import UserLayout from './components/user/UserLayout';
import UserDashboard from './pages/user/UserDashboard';
import UserChat from './pages/user/UserChat';
import UserProfile from './pages/user/UserProfile';
import FavoritesPage from './pages/user/FavoritesPage';

import AuthPage from './pages/user/AuthPage';
import CharacterProfile from './pages/user/CharacterProfile';
import { useAuthStore } from './store/authStore';

const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const { isAuthenticated } = useAuthStore();
  if (!isAuthenticated) {
    return <Navigate to="auth" replace />;
  }
  return children;
};

function UserApp() {
  return (
    <Routes>
      <Route path="auth" element={<AuthPage />} />
      <Route 
        path="/"
        element={
          <ProtectedRoute>
            <UserLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<UserDashboard />} />
        <Route path="profile" element={<UserProfile />} />
        <Route path="favorites" element={<FavoritesPage />} />
        <Route path="character/:characterId" element={<CharacterProfile />} />
      </Route>
      <Route 
        path="/chat/:characterId"
        element={
          <ProtectedRoute>
            <UserChat />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default UserApp;