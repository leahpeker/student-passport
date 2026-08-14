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
        className="rounded-lg border border-red-800/60 bg-red-950/40 px-4 py-3 text-red-300"
      >
        {label} could not be loaded. {error}
      </p>
    );
  }
  if (loading) {
    return (
      <p role="status" className="py-8 text-muted">
        Loading {label}…
      </p>
    );
  }
  return null;
}
