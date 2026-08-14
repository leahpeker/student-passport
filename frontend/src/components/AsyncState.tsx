/** Shared loading and error presentation for a client call. */
export function AsyncState({
  loading,
  error,
  label,
}: {
  loading: boolean;
  error: string | null;
  label: string;
}) {
  if (error) {
    return (
      <p
        role="alert"
        className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-800"
      >
        {label} could not be loaded. {error}
      </p>
    );
  }
  if (loading) {
    return (
      <p role="status" className="py-8 text-slate-500">
        Loading {label}…
      </p>
    );
  }
  return null;
}
