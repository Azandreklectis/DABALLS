interface TimestampProps {
  value?: string | number | Date | null;
  format?: 'relative' | 'absolute';
  fallback?: string;
  className?: string;
}

function Timestamp({
  value,
  format = 'absolute',
  fallback = 'Not available',
  className = '',
}: TimestampProps) {
  if (value === undefined || value === null || value === '') {
    return <span className={className}>{fallback}</span>;
  }

  const date = value instanceof Date ? value : new Date(value);

  if (Number.isNaN(date.getTime())) {
    return <span className={className}>{fallback}</span>;
  }

  const absolute = new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);

  if (format === 'absolute') {
    return (
      <time className={className} dateTime={date.toISOString()}>
        {absolute}
      </time>
    );
  }

  const seconds = Math.round((date.getTime() - Date.now()) / 1000);
  const absoluteSeconds = Math.abs(seconds);

  let amount: number;
  let unit: Intl.RelativeTimeFormatUnit;

  if (absoluteSeconds < 60) {
    amount = seconds;
    unit = 'second';
  } else if (absoluteSeconds < 3600) {
    amount = Math.round(seconds / 60);
    unit = 'minute';
  } else if (absoluteSeconds < 86400) {
    amount = Math.round(seconds / 3600);
    unit = 'hour';
  } else {
    amount = Math.round(seconds / 86400);
    unit = 'day';
  }

  const relative = new Intl.RelativeTimeFormat(undefined, {
    numeric: 'auto',
  }).format(amount, unit);

  return (
    <time
      className={className}
      dateTime={date.toISOString()}
      title={absolute}
    >
      {relative}
    </time>
  );
}

export default Timestamp;