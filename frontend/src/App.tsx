import { BrowserRouter, Routes, Route, NavLink, useNavigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './lib/queryClient';
import Overview from './pages/Overview';
import Gigs from './pages/Gigs';
import Orders from './pages/Orders';
import Messages from './pages/Messages';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import Logs from './pages/Logs';
import {
  LayoutDashboard,
  FileText,
  Mail,
  DollarSign,
  BarChart,
  Settings as SettingsIcon,
  ClipboardList,
} from 'lucide-react';

const navItems = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/gigs', label: 'Gigs', icon: FileText },
  { to: '/orders', label: 'Orders', icon: DollarSign },
  { to: '/messages', label: 'Messages', icon: Mail },
  { to: '/analytics', label: 'Analytics', icon: BarChart },
  { to: '/settings', label: 'Settings', icon: SettingsIcon },
  { to: '/logs', label: 'Logs', icon: ClipboardList },
];

function NavLinkItem({ to, label, Icon }: { to: string; label: string; Icon: React.ComponentType }) {
  const navigate = useNavigate();
  return (
    <NavLink
      to={to}
      onClick={() => navigate(to)}
      className={({ isActive }) =>
        `px-4 py-2 rounded-md text-sm font-medium transition-colors ${
          isActive
            ? 'bg-blue-100 text-blue-700 shadow-sm'
            : 'text-gray-600 hover:bg-gray-100'
        }`
      }
    >
      <Icon size={18} className="mr-2" />
      {label}
    </NavLink>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50 text-gray-900">
          <nav className="bg-white border-b border-gray-200 px-4 py-3 sticky top-0 z-20">
            <div className="max-w-6xl mx-auto flex items-center gap-6">
              <span className="font-bold text-xl tracking-tight">Fiverr Agent</span>
              <div className="flex gap-2">{navItems.map((item) => (
                <NavLinkItem key={item.to} {...item} />
              ))}</div>
            </div>
          </nav>

          <main className="max-w-6xl mx-auto px-4 py-6">
            <Routes>
              <Route path="/" element={<Overview />} />
              <Route path="/gigs" element={<Gigs />} />
              <Route path="/orders" element={<Orders />} />
              <Route path="/messages" element={<Messages />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/logs" element={<Logs />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
