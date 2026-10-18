import type { HTMLAttributes } from 'react';

export type StatusType =
  | 'online'
  | 'offline'
  | 'busy'
  | 'warning'
  | 'unknown';

interface StatusDotProps extends HTMLAttributes<HTMLSpanElement> {
  status: StatusType;
  label?: string;
  pulse?: boolean;
}

function StatusDot({
  status,
  label,
  pulse = false,
  className = '',
  ...props
}: StatusDotProps) {
  const classes = [
    'status-dot',
    `status-dot--${status}`,
    pulse ? 'status-dot--pulse' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <span className={classes} {...props}>
      <span className="status-dot__indicator" aria-hidden="true" />
      {label && <span className="status-dot__label">{label}</span>}
    </span>
  );
}

export default StatusDot;