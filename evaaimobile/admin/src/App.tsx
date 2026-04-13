import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import useAuthStore from './store/useAuthStore';
import PrivateRoute from './components/PrivateRoute';
import Sidebar from './components/Sidebar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Users from './pages/Users';
import Settings from './pages/Settings';
import Characters from './pages/Characters';
import CharacterPage from './pages/CharacterPage';
import Profile from './components/character/Profile';
import Layers from './components/character/Layers';
import Content from './components/character/Content';
import Prompts from './components/character/Prompts';
import Dialogue from './components/character/Dialogue';
import Voice from './components/character/Voice';
import References from './components/character/References';
import Tokens from './pages/Tokens';
import Logs from './pages/Logs';
import ComfyWorkflows from './pages/ComfyWorkflows';

function App() {
  return (
    <Router>
      <div className="flex h-screen bg-gray-100">
        <Sidebar />
        <main className="flex-1 p-6 overflow-y-auto">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route element={<PrivateRoute />}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/users" element={<Users />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/tokens" element={<Tokens />} />
              <Route path="/logs" element={<Logs />} />
              <Route path="/characters" element={<Characters />} />
              <Route path="/characters/:id/*" element={<CharacterPage />} />
              <Route path="/comfy-workflows" element={<ComfyWorkflows />} />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Route>
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
