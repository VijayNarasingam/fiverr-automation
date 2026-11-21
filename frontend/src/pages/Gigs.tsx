import { useGigs, usePublishGigs } from '../hooks/useGigs';
import { Play } from 'lucide-react';

function statusBadge(status: string): JSX.Element {
  const lower = status.toLowerCase();
  const classMap: Record<string, string> = {
    published: 'badge-published',
    pending: 'badge-pending',
    draft: 'badge-draft',
  };
  const cls = classMap[lower] || 'badge';
  return <span className={cls}>{status}</span>;
}

export default function Gigs() {
  const { data: gigs = [], isPending: isLoading } = useGigs();
  const publish = usePublishGigs();

  const handlePublish = () => {
    publish.mutate();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="page-title">Gigs</h1>
          <p className="text-gray-500 text-sm mt-1">
            Manage your Fiverr gigs. Publish pending gigs to go live.
          </p>
        </div>
        <button
          className="btn-success"
          onClick={handlePublish}
          disabled={publish.isPending}
        >
          {publish.isPending ? (
            <>
              Publishing <span className="animate-spin">⟳</span>
            </>
          ) : (
            <>
              <Play size={16} /> Publish Pending Gigs
            </>
          )}
        </button>
      </div>

      <div className="table-wrapper">
        <table className="w-full text-left">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="px-6 py-3 text-sm font-semibold text-gray-700">
                Title
              </th>
              <th className="px-6 py-3 text-sm font-semibold text-gray-700">
                Category
              </th>
              <th className="px-6 py-3 text-sm font-semibold text-gray-700">
                Status
              </th>
              <th className="px-6 py-3 text-sm font-semibold text-gray-700">
                Gig URL
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {isLoading ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                  Loading gigs...
                </td>
              </tr>
            ) : gigs.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                  No gigs found.
                </td>
              </tr>
            ) : (
              gigs.map((gig) => (
                <tr key={gig.id}>
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">
                    {gig.title}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {gig.category}
                  </td>
                  <td className="px-6 py-4 text-sm">{statusBadge(gig.status)}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {gig.gig_url ? (
                      <a
                        href={gig.gig_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline"
                      >
                        Open
                      </a>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {publish.isError && (
        <div className="p-3 rounded-md bg-red-50 border border-red-200 text-red-800 text-sm">
          Failed to publish gigs. Please try again.
        </div>
      )}
    </div>
  );
}
