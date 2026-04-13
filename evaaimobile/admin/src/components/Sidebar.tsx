import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import useAuthStore from '../store/useAuthStore';
import { Users, LayoutDashboard, Settings, LogOut, ChevronsUpDown, Plus, Bot, Ticket, FileText } from 'lucide-react';

const characters = [
  { id: 'eva', name: 'Ева' },
  { id: 'luna', name: 'Луна' },
];

const Sidebar: React.FC = () => {
  const { logout } = useAuthStore();
  const location = useLocation();
  const [isCharactersOpen, setIsCharactersOpen] = useState(true);

  const handleLogout = () => {
    logout();
  };

  const isActive = (path: string) => location.pathname.startsWith(path);

  return (
    <div className="w-64 bg-gray-900 text-gray-200 p-4 flex flex-col h-full">
      <div className="flex-1">
        <h2 className="text-2xl font-bold mb-6 text-white">EVA AI Admin</h2>
        <nav>
          <ul className="space-y-2">
            <li>
              <NavLink 
                to="/dashboard"
                end
                className={({ isActive }) => 
                  `flex items-center p-3 rounded-lg transition-colors ${
                    isActive 
                      ? 'bg-indigo-600 text-white' 
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`
                }
              >
                <LayoutDashboard className="w-5 h-5 mr-3" />
                Dashboard
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/characters"
                className={({ isActive }) => 
                  `flex items-center p-3 rounded-lg transition-colors ${
                    isActive 
                      ? 'bg-indigo-600 text-white' 
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`
                }
              >
                <Bot className="w-5 h-5 mr-3" />
                Characters
              </NavLink>
            </li>
             <li>
              <NavLink 
                to="/users"
                className={({ isActive }) => 
                  `flex items-center p-3 rounded-lg transition-colors ${
                    isActive 
                      ? 'bg-indigo-600 text-white' 
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`
                }
              >
                <Users className="w-5 h-5 mr-3" />
                Users
              </NavLink>
            </li>
            <li>
              <NavLink 
                to="/tokens"
                className={({ isActive }) => 
                  `flex items-center p-3 rounded-lg transition-colors ${
                    isActive 
                      ? 'bg-indigo-600 text-white' 
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`
                }
              >
                <Ticket className="w-5 h-5 mr-3" />
                Tokens
              </NavLink>
            </li>
            <li>
              <NavLink 
                to="/logs"
                className={({ isActive }) => 
                  `flex items-center p-3 rounded-lg transition-colors ${
                    isActive 
                      ? 'bg-indigo-600 text-white' 
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`
                }
              >
                <FileText className="w-5 h-5 mr-3" />
                Logs
              </NavLink>
            </li>
            <li>
              <NavLink 
                to="/comfy-workflows"
                className={({ isActive }) => 
                  `flex items-center p-3 rounded-lg transition-colors ${
                    isActive 
                      ? 'bg-indigo-600 text-white' 
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`
                }
              >
                <Bot className="w-5 h-5 mr-3" />
                Comfy Workflows
              </NavLink>
            </li>
            <li>
              <NavLink 
                to="/settings"
                className={({ isActive }) => 
                  `flex items-center p-3 rounded-lg transition-colors ${
                    isActive 
                      ? 'bg-indigo-600 text-white' 
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`
                }
              >
                <Settings className="w-5 h-5 mr-3" />
                Settings
              </NavLink>
            </li>
          </ul>
        </nav>
      </div>
      
      <div className="mt-auto">
        <button
          onClick={handleLogout}
          className="flex items-center w-full p-3 text-gray-300 rounded-lg hover:bg-gray-700 hover:text-white transition-colors"
        >
          <LogOut className="w-5 h-5 mr-3" />
          Logout
        </button>
      </div>
    </div>
  );
};

export default Sidebar;