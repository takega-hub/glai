import React, { useState, useEffect } from 'react';
import { Users, MessageSquare, Gift, TrendingUp, DollarSign } from 'lucide-react';
import useAuthStore from '../store/useAuthStore';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface AnalyticsData {
  user_analytics: {
    total_users: number;
    active_users_7d: number;
    active_users_30d: number;
    new_users_7d: number;
    new_users_30d: number;
    retention_rate_7d: number;
    retention_rate_30d: number;
  };
  revenue_analytics: {
    total_revenue_7d: number;
    total_revenue_30d: number;
    total_revenue_lifetime: number;
    average_revenue_per_user: number;
    top_packages: Array<{
      name: string;
      purchase_count: number;
      total_revenue: number;
    }>;
    revenue_by_day: Array<{
      date: string;
      revenue: number;
    }>;
  };
  system_health: {
    database_status: string;
    api_response_time: number;
    active_connections: number;
    error_rate: number;
    uptime_percentage: number;
  };
}

interface CharacterPopularity {
  name: string;
  user_count: number;
}

const Dashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [characterPopularity, setCharacterPopularity] = useState<CharacterPopularity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { token } = useAuthStore();

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    if (!token) return;

    try {
      setIsLoading(true);
      setError(null);

      // Fetch user analytics
      const userResponse = await fetch('/api/analytics/users', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!userResponse.ok) {
        throw new Error('Failed to fetch user analytics');
      }

      const userAnalytics = await userResponse.json();

      // Fetch revenue analytics
      const revenueResponse = await fetch('/api/analytics/revenue?days=30', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!revenueResponse.ok) {
        throw new Error('Failed to fetch revenue analytics');
      }

      const revenueAnalytics = await revenueResponse.json();

      // Fetch system health
      const healthResponse = await fetch('/api/analytics/system-health', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!healthResponse.ok) {
        throw new Error('Failed to fetch system health');
      }

      const systemHealth = await healthResponse.json();

      // Fetch character popularity
      const popularityResponse = await fetch('/api/analytics/characters/popularity', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!popularityResponse.ok) {
        throw new Error('Failed to fetch character popularity');
      }

      const popularityData = await popularityResponse.json();
      setCharacterPopularity(popularityData);

      setAnalytics({
        user_analytics: userAnalytics,
        revenue_analytics: revenueAnalytics,
        system_health: systemHealth,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch analytics');
      console.error('Error fetching analytics:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[...Array(4)].map((_, index) => (
            <div key={index} className="bg-white p-6 rounded-lg shadow-md animate-pulse">
              <div className="flex items-center">
                <div className="w-12 h-12 bg-gray-300 rounded-full mr-4"></div>
                <div>
                  <div className="h-4 bg-gray-300 rounded w-20 mb-2"></div>
                  <div className="h-8 bg-gray-300 rounded w-16"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6 animate-pulse">
            <div className="h-6 bg-gray-300 rounded w-32 mb-4"></div>
            <div className="space-y-3">
              {[...Array(5)].map((_, index) => (
                <div key={index} className="h-4 bg-gray-300 rounded"></div>
              ))}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6 animate-pulse">
            <div className="h-6 bg-gray-300 rounded w-32 mb-4"></div>
            <div className="space-y-3">
              {[...Array(5)].map((_, index) => (
                <div key={index} className="h-4 bg-gray-300 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading dashboard</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
              <div className="mt-4">
                <button
                  onClick={fetchAnalytics}
                  className="text-sm font-medium text-red-600 hover:text-red-500"
                >
                  Try again
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return null;
  }

  const statCards = [
    {
      title: 'Total Users',
      value: analytics.user_analytics.total_users,
      icon: Users,
      color: 'bg-blue-500',
    },
    {
      title: 'Active Users (7d)',
      value: analytics.user_analytics.active_users_7d,
      icon: TrendingUp,
      color: 'bg-green-500',
    },
    {
      title: 'Active Users (30d)',
      value: analytics.user_analytics.active_users_30d,
      icon: MessageSquare,
      color: 'bg-purple-500',
    },
    {
      title: 'Total Revenue',
      value: `$${analytics.revenue_analytics.total_revenue_lifetime.toLocaleString()}`,
      icon: DollarSign,
      color: 'bg-orange-500',
    },
  ];

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <button
          onClick={fetchAnalytics}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          Refresh Data
        </button>
      </div>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map((stat, index) => (
          <div key={index} className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
            <div className="flex items-center">
              <div className={`${stat.color} p-3 rounded-full mr-4`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500">{stat.title}</h3>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* System Health */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">System Health</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {analytics.system_health.uptime_percentage}%
            </div>
            <div className="text-sm text-gray-500">Uptime</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {analytics.system_health.api_response_time}ms
            </div>
            <div className="text-sm text-gray-500">API Response Time</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {analytics.system_health.active_connections}
            </div>
            <div className="text-sm text-gray-500">Active DB Connections</div>
          </div>
        </div>
        <div className="mt-4 flex items-center">
          <div className={`w-3 h-3 rounded-full mr-2 ${
            analytics.system_health.database_status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
          }`}></div>
          <span className="text-sm text-gray-600">
            Database Status: {analytics.system_health.database_status}
          </span>
        </div>
      </div>

      {/* Revenue Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold mb-4">Revenue Overview</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Revenue (7 days)</span>
              <span className="font-semibold">${analytics.revenue_analytics.total_revenue_7d.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Revenue (30 days)</span>
              <span className="font-semibold">${analytics.revenue_analytics.total_revenue_30d.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Average Revenue per User</span>
              <span className="font-semibold">${analytics.revenue_analytics.average_revenue_per_user.toFixed(2)}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold mb-4">User Retention</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">7-day Retention Rate</span>
              <span className="font-semibold">{analytics.user_analytics.retention_rate_7d.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">30-day Retention Rate</span>
              <span className="font-semibold">{analytics.user_analytics.retention_rate_30d.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">New Users (30 days)</span>
              <span className="font-semibold">{analytics.user_analytics.new_users_30d}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Character Popularity */}
      <div className="bg-white rounded-lg shadow-md p-6 mt-8">
        <h2 className="text-lg font-semibold mb-4">Character Popularity</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={characterPopularity}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="user_count" fill="#8884d8" name="User Count" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default Dashboard;