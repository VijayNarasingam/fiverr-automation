import { useState } from 'react';
import { useSettings, useUpdateSettings } from '../hooks/useSettings';
import { Save } from 'lucide-react';

export default function Settings() {
  const { data, isPending: isLoading } = useSettings();
  const updateSettings = useUpdateSettings();

  const [form, setForm] = useState({
    rate_limit_per_hour: String(data?.rate_limit_per_hour ?? 3),
    max_gigs_per_run: String(data?.max_gigs_per_run ?? 2),
    ollama_base_url: data?.ollama_base_url ?? 'http://localhost:11434/v1',
    discord_configured: Boolean(data?.discord_configured),
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target as HTMLInputElement;
    setForm((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    // ``discord_configured`` is read-only (derived from DISCORD_WEBHOOK_URL),
    // so only the editable fields are submitted.
    updateSettings.mutate({
      rate_limit_per_hour: Number(form.rate_limit_per_hour),
      max_gigs_per_run: Number(form.max_gigs_per_run),
      ollama_base_url: form.ollama_base_url,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="text-gray-500 text-sm mt-1">
            Configure rate limits, gigs per run, Ollama, and notifications.
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="stat-card p-8 text-center text-gray-500">
          Loading settings...
        </div>
      ) : (
        <form onSubmit={handleSave} className="space-y-4">
          <div className="table-wrapper">
            <div className="px-6 py-4 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-700">Rate limits</h2>
              <p className="text-xs text-gray-500 mt-1">
                Maximum automated actions per hour and per run.
              </p>
            </div>
            <div className="px-6 py-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Rate limit (per hour)
                </label>
                <input
                  name="rate_limit_per_hour"
                  type="number"
                  value={form.rate_limit_per_hour}
                  onChange={handleChange}
                  className="input"
                  min="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max gigs per run
                </label>
                <input
                  name="max_gigs_per_run"
                  type="number"
                  value={form.max_gigs_per_run}
                  onChange={handleChange}
                  className="input"
                  min="0"
                />
              </div>
            </div>
          </div>

          <div className="table-wrapper">
            <div className="px-6 py-4 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-700">AI provider</h2>
              <p className="text-xs text-gray-500 mt-1">
                Base URL of the local Ollama API.
              </p>
            </div>
            <div className="px-6 py-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Ollama base URL
              </label>
              <input
                name="ollama_base_url"
                type="url"
                value={form.ollama_base_url}
                onChange={handleChange}
                className="input"
              />
            </div>
          </div>

          <div className="table-wrapper">
            <div className="px-6 py-4 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-700">
                Notifications
              </h2>
              <p className="text-xs text-gray-500 mt-1">
                Discord alerts are based on the configured webhook URL.
              </p>
            </div>
            <div className="px-6 py-4 flex items-center gap-3">
              <input
                id="discord_configured"
                name="discord_configured"
                type="checkbox"
                checked={form.discord_configured}
                onChange={handleChange}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="discord_configured" className="text-sm text-gray-700">
                Discord configured
              </label>
              <span className="ml-2 text-xs text-gray-500">
                {form.discord_configured ? 'Webhook URL set' : 'Not set'}
              </span>
            </div>
          </div>

          <button
            type="submit"
            disabled={updateSettings.isPending}
            className="btn-primary"
          >
            {updateSettings.isPending ? 'Saving...' : (
              <>
                <Save size={16} /> Save settings
              </>
            )}
          </button>

          {updateSettings.isError && (
            <div className="p-3 rounded-md bg-red-50 border border-red-200 text-red-800 text-sm">
              Failed to save settings. Please try again.
            </div>
          )}
        </form>
      )}
    </div>
  );
}
