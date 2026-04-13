import { Navigate, Outlet } from 'react-router-dom';
import useAuthStore from '../store/useAuthStore';
import { jwtDecode } from 'jwt-decode';

interface DecodedToken {
  user_id: string;
  role: string;
  expires: number;
}

const PrivateRoute = () => {
  const { token, setToken } = useAuthStore();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  try {
    const decodedToken: DecodedToken = jwtDecode(token);
    const isExpired = decodedToken.expires * 1000 < Date.now();
    const isAdmin = decodedToken.role === 'admin' || decodedToken.role === 'super_admin';

    if (isExpired) {
      setToken(null);
      return <Navigate to="/login" replace />;
    }

    if (!isAdmin) {
      // You can create a dedicated 'Unauthorized' page or redirect to login
      return <Navigate to="/login" replace />;
    }

  } catch (error) {
    console.error('Invalid token:', error);
    setToken(null);
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
};

export default PrivateRoute;
