import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { Order } from '../types';

export const ORDERS_QUERY_KEY = ['orders'];

export function useOrders() {
  return useQuery({
    queryKey: ORDERS_QUERY_KEY,
    queryFn: async (): Promise<Order[]> => {
      const { data } = await api.get<Order[]>('/orders');
      return data;
    },
  });
}
