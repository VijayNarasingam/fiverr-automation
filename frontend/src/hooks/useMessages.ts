import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { Message, SendMessageInput } from '../types';

export const MESSAGES_QUERY_KEY = ['messages'];

export function useMessages() {
  return useQuery({
    queryKey: MESSAGES_QUERY_KEY,
    queryFn: async (): Promise<Message[]> => {
      const { data } = await api.get<Message[]>('/messages');
      return data;
    },
  });
}

export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: SendMessageInput): Promise<Message> => {
      const { data } = await api.post<Message>('/messages', input);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MESSAGES_QUERY_KEY });
    },
  });
}
