import type { ReactNode } from 'react';

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

function EmptyState({
  title,
  description,
  action,
  className = '',
}: EmptyStateProps) {
  return (
    <section
      className={`empty-state ${className}`.trim()}
      aria-label={title}
    >
      <span className="empty-state__mark" aria-hidden="true">
        —
      </span>

      <h3 className="empty-state__title">{title}</h3>

      {description && (
        <p className="empty-state__description">{description}</p>
      )}

      {action && <div className="empty-state__action">{action}</div>}
    </section>
  );
}

export default EmptyState;