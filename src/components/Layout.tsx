import { Link, Outlet } from 'react-router-dom';

const Layout = () => {
  return (
    <div className="flex h-screen bg-gray-100">
      <aside className="w-64 bg-gray-800 text-white p-4">
        <h1 className="text-2xl font-bold mb-4">EVA AI Admin</h1>
        <nav>
          <ul>
            <li className="mb-2"><Link to="/">Dashboard</Link></li>
            <li className="mb-2"><Link to="/users">Users</Link></li>
            <li className="mb-2"><Link to="/characters">Characters</Link></li>
          </ul>
        </nav>
      </aside>
      <main className="flex-1 p-8">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
