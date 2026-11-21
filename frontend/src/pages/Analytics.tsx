import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { AnalyticsOverview, GigPerformance } from '../types';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar,
} from 'recharts';

const ANALYTICS_OVERVIEW_QUERY_KEY = ['analytics', 'overview'];
const GIG_PERFORMANCE_QUERY_KEY = ['analytics', 'gig-performance'];

async function fetchOverview(): Promise<AnalyticsOverview> {
  return api.get<AnalyticsOverview>('/analytics/overview').then((res) => res.data);
}

async function fetchGigPerformance(): Promise<GigPerformance[]> {
  return api.get<GigPerformance[]>('/analytics/gig-performance').then(
    (res) => res.data
  );
}

// Illustrative orders-over-time series. A backend time-series endpoint is not
// yet wired up, so this shows the chart shape with sample data.
const ORDERS_OVER_TIME = [
  { name: 'Mon', orders: 3 },
  { name: 'Tue', orders: 5 },
  { name: 'Wed', orders: 2 },
  { name: 'Thu', orders: 7 },
  { name: 'Fri', orders: 4 },
  { name: 'Sat', orders: 6 },
  { name: 'Sun', orders: 3 },
];

export default function Analytics() {
  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ANALYTICS_OVERVIEW_QUERY_KEY,
    queryFn: fetchOverview,
  });
  const {
    data: performance = [],
    isLoading: perfLoading,
  } = useQuery({
    queryKey: GIG_PERFORMANCE_QUERY_KEY,
    queryFn: fetchGigPerformance,
  });

  const loading = overviewLoading || perfLoading;
  const revenueDollars = (overview?.revenue_cents ?? 0) / 100;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title">Analytics</h1>
        <p className="text-gray-500 text-sm mt-1">
          Gig performance and A/B test insights for your Fiverr automation agent.
        </p>
      </div>

      {loading ? (
        <div className="stat-card p-8 text-center text-gray-500">
          Loading analytics...
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-4">
            <div className="stat-card">
              <p className="stat-label">Total Gigs</p>
              <p className="stat-value">{overview?.gigs ?? 0}</p>
            </div>
            <div className="stat-card">
              <p className="stat-label">Total Orders</p>
              <p className="stat-value">{overview?.orders ?? 0}</p>
            </div>
            <div className="stat-card">
              <p className="stat-label">Revenue</p>
              <p className="stat-value">${revenueDollars.toFixed(2)}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="chart-card">
              <h2 className="chart-title">Orders Over Time</h2>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={ORDERS_OVER_TIME}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Line dataKey="orders" stroke="#4f46e5" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="chart-card">
              <h2 className="chart-title">Orders per Gig</h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={performance}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="title" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="order_count" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
