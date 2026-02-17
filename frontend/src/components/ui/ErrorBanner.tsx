interface ErrorBannerProps {
  message: string | null;
  onDismiss: () => void;
}

export function ErrorBanner({ message, onDismiss }: ErrorBannerProps) {
  if (!message) return null;

  return (
    <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded flex items-center justify-between">
      <span className="text-sm">{message}</span>
      <button
        type="button"
        onClick={onDismiss}
        className="ml-4 text-red-500 hover:text-red-700 text-lg leading-none cursor-pointer"
        aria-label="Dismiss error"
      >
        &times;
      </button>
    </div>
  );
}
