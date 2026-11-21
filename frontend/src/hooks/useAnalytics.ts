import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { AnalyticsOverview, GigPerformance } from '../types';

export const ANALYTICS_OVERVIEW_QUERY_KEY = ['analytics', 'overview'];
export const GIG_PERFORMANCE_QUERY_KEY = ['analytics', 'gig-performance'];

async function fetchOverview(): Promise<AnalyticsOverview> {
  const { data } = await api.get<AnalyticsOverview>('/analytics/overview');
  return data;
}

async function fetchGigPerformance(): Promise<GigPerformance[]> {
  const { data } = await api.get<GigPerformance[]>('/analytics/gig-performance');
  return data;
}

export function useAnalyticsOverview() {
  return useQuery({
    queryKey: ANALYTICS_OVERVIEW_QUERY_KEY,
    queryFn: fetchOverview,
  });
}

export function useGigPerformance() {
  return useQuery({
    queryKey: GIG_PERFORMANCE_QUERY_KEY,
    queryFn: fetchGigPerformance,
  });
}
