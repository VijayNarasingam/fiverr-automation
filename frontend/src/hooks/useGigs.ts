import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { Gig } from '../types';

export const GIGS_QUERY_KEY = ['gigs'];

export function useGigs() {
  return useQuery({
    queryKey: GIGS_QUERY_KEY,
    queryFn: async (): Promise<Gig[]> => {
      const { data } = await api.get<Gig[]>('/gigs');
      return data;
    },
  });
}

export function usePublishGigs() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (): Promise<unknown> => {
      const { data } = await api.post('/gigs/publish');
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: GIGS_QUERY_KEY });
    },
  });
}
