import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Users from './pages/Users';
import Characters from './pages/Characters';
import UserApp from './UserApp';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="users" element={<Users />} />
        <Route path="characters" element={<Characters />} />
      </Route>
      <Route path="/user/*" element={<UserApp />} />
    </Routes>
  );
}

export default App;
