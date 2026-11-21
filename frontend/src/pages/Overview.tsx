import { useQuery } from '@tanstack/react-query';
import { useGigs } from '../hooks/useGigs';
import { api } from '../lib/api';
import type { AnalyticsOverview } from '../types';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

const ANALYTICS_QUERY_KEY = ['analytics', 'overview'];

function fetchOverview(): Promise<AnalyticsOverview> {
  return api.get<AnalyticsOverview>('/analytics/overview').then((res) => res.data);
}

export default function Overview() {
  const { data: gigs = [], isLoading: gigsLoading } = useGigs();
  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ANALYTICS_QUERY_KEY,
    queryFn: fetchOverview,
  });

  const totalGigs = overview?.gigs ?? gigs.length;
  const publishedGigs = gigs.filter((g) => g.status.toLowerCase() === 'published').length;
  const revenueDollars = (overview?.revenue_cents ?? 0) / 100;

  const loading = gigsLoading || overviewLoading;

  const statusCounts: Record<string, number> = {};
  gigs.forEach((g) => {
    statusCounts[g.status] = (statusCounts[g.status] ?? 0) + 1;
  });
  const chartData = Object.entries(statusCounts).map(([status, count]) => ({
    status,
    count,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title">Overview</h1>
        <p className="text-gray-500 text-sm mt-1">
          High-level summary of your Fiverr automation agent.
        </p>
      </div>

      {loading ? (
        <div className="stat-card p-8 text-center text-gray-500">
          Loading dashboard...
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="stat-card">
              <p className="stat-label">Total Gigs</p>
              <p className="stat-value">{totalGigs}</p>
            </div>
            <div className="stat-card">
              <p className="stat-label">Published</p>
              <p className="stat-value">{publishedGigs}</p>
            </div>
            <div className="stat-card">
              <p className="stat-label">Revenue</p>
              <p className="stat-value">${revenueDollars.toFixed(2)}</p>
            </div>
          </div>

          <div className="table-wrapper">
            <div className="px-6 py-4 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-700">Gigs by status</h2>
            </div>
            <div className="p-4">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="status" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
