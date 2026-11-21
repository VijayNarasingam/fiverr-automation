import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';

export const SETTINGS_QUERY_KEY = ['settings'];

export interface Settings {
  rate_limit_per_hour: number;
  max_gigs_per_run: number;
  ollama_base_url: string;
  discord_configured: boolean;
  [key: string]: unknown;
}

export function useSettings() {
  return useQuery({
    queryKey: SETTINGS_QUERY_KEY,
    queryFn: async (): Promise<Settings> => {
      const { data } = await api.get<Settings>('/settings');
      return data;
    },
  });
}

export function useUpdateSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (updates: Record<string, unknown>): Promise<unknown> => {
      const { data } = await api.post('/settings', updates);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEY });
    },
  });
}
