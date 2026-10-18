interface LoadingStateProps {
  label?: string;
  className?: string;
}

function LoadingState({
  label = 'Loading data…',
  className = '',
}: LoadingStateProps) {
  return (
    <div
      className={`loading-state ${className}`.trim()}
      role="status"
      aria-live="polite"
    >
      <span className="loading-state__spinner" aria-hidden="true" />
      <span className="loading-state__label">{label}</span>
    </div>
  );
}

export default LoadingState;