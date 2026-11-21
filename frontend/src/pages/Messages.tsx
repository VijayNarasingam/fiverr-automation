import { useMessages, useSendMessage } from '../hooks/useMessages';
import type { SendMessageInput } from '../types';
import { Send, Mail } from 'lucide-react';

function directionBadge(direction: string): JSX.Element {
  const lower = direction.toLowerCase();
  const cls = lower === 'inbound' ? 'badge-inbound' : 'badge-outbound';
  const label = lower === 'inbound' ? 'Inbound' : 'Outbound';
  return <span className={cls}>{label}</span>;
}

export default function Messages() {
  const { data: messages = [], isPending: isLoading } = useMessages();
  const send = useSendMessage();

  const [direction, setDirection] = React.useState<string>('outbound');
  const [content, setContent] = React.useState<string>('');
  const [orderId, setOrderId] = React.useState<string>('');

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;
    send.mutate({
      direction,
      content,
      order_id: orderId.trim() ? Number(orderId) : null,
    });
    setContent('');
    setOrderId('');
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div>
          <h1 className="page-title">Messages</h1>
          <p className="text-gray-500 text-sm mt-1">
            Read and send messages related to your orders.
          </p>
        </div>
      </div>

      <div className="table-wrapper">
        <table className="w-full text-left">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="px-6 py-3 text-sm font-semibold text-gray-700">
                Direction
              </th>
              <th className="px-6 py-3 text-sm font-semibold text-gray-700">
                Content
              </th>
              <th className="px-6 py-3 text-sm font-semibold text-gray-700">
                Order ID
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {isLoading ? (
              <tr>
                <td colSpan={3} className="px-6 py-8 text-center text-gray-500">
                  Loading messages...
                </td>
              </tr>
            ) : messages.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-6 py-8 text-center text-gray-500">
                  No messages found.
                </td>
              </tr>
            ) : (
              messages.map((message) => (
                <tr key={message.id}>
                  <td className="px-6 py-4 text-sm">{directionBadge(message.direction)}</td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {message.content}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {message.order_id ?? '—'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="table-wrapper p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Send a message</h2>
        <form onSubmit={handleSend} className="grid grid-cols-1 sm:grid-cols-4 gap-3 items-end">
          <select
            value={direction}
            onChange={(e) => setDirection(e.target.value)}
            className="input"
          >
            <option value="outbound">Outbound</option>
            <option value="inbound">Inbound</option>
          </select>
          <input
            type="text"
            placeholder="Order ID (optional)"
            value={orderId}
            onChange={(e) => setOrderId(e.target.value)}
            className="input"
          />
          <textarea
            placeholder="Message content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="input min-h-[80px]"
          />
          <button
            type="submit"
            className="btn-primary"
            disabled={send.isPending || !content.trim()}
          >
            {send.isPending ? 'Sending...' : <><Send size={16} /> Send</>}
          </button>
        </form>
      </div>

      {send.isError && (
        <div className="p-3 rounded-md bg-red-50 border border-red-200 text-red-800 text-sm">
          Failed to send message. Please try again.
        </div>
      )}
    </div>
  );
}
