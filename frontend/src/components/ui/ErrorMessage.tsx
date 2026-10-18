import type { ReactNode } from 'react';

interface ErrorMessageProps {
  title?: string;
  message: string;
  action?: ReactNode;
  className?: string;
}

function ErrorMessage({
  title = 'Something went wrong',
  message,
  action,
  className = '',
}: ErrorMessageProps) {
  return (
    <section
      className={`error-message ${className}`.trim()}
      role="alert"
    >
      <div className="error-message__content">
        <p className="error-message__title">{title}</p>
        <p className="error-message__description">{message}</p>
      </div>

      {action && <div className="error-message__action">{action}</div>}
    </section>
  );
}

export default ErrorMessage;