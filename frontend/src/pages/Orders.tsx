import { useOrders } from '../hooks/useOrders';
import { DollarSign } from 'lucide-react';

function statusBadge(status: string): JSX.Element {
  const lower = status.toLowerCase();
  const classMap: Record<string, string> = {
    delivered: 'badge-delivered',
    completed: 'badge-completed',
    cancelled: 'badge-cancelled',
    pending: 'badge-pending',
  };
  const cls = classMap[lower] || 'badge';
  return <span className={cls}>{status}</span>;
}

export default function Orders() {
  const { data: orders = [], isPending: isLoading } = useOrders();

  const totalAmount = orders.reduce((sum, o) => sum + o.amount, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <div>
          <h1 className="page-title">Orders</h1>
          <p className="text-gray-500 text-sm mt-1">
            Track buyer orders, amounts, and fulfillment status.
          </p>
        </div>
        <div className="stat-card flex items-center gap-3">
          <DollarSign size={20} className="text-gray-500" />
          <div>
            <p className="stat-label">Total order value</p>
            <p className="stat-value">${totalAmount.toFixed(2)}</p>
          </div>
        </div>
      </div>

      <div className="table-wrapper">
        <table className="w-full text-left">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="px-6 py-3 text-sm font-semibold text-gray-700">
                Buyer
              </th>
              <th className="px-6 py-3 text-sm font-semibold text-gray-700">
                Amount
              </th>
              <th className="px-6 py-3 text-sm font-semibold text-gray-700">
                Status
              </th>
              <th className="px-6 py-3 text-sm font-semibold text-gray-700">
                Fiverr Order ID
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {isLoading ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                  Loading orders...
                </td>
              </tr>
            ) : orders.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                  No orders found.
                </td>
              </tr>
            ) : (
              orders.map((order) => (
                <tr key={order.id}>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {order.buyer_username ?? '—'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    ${order.amount.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 text-sm">{statusBadge(order.status)}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {order.fiverr_order_id ?? '—'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
