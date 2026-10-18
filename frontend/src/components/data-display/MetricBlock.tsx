import type { ReactNode } from 'react';

type MetricTone = 'default' | 'positive' | 'warning' | 'negative';

interface MetricBlockProps {
  label: string;
  value: string | number;
  unit?: string;
  detail?: string;
  tone?: MetricTone;
  icon?: ReactNode;
  className?: string;
}

function MetricBlock({
  label,
  value,
  unit,
  detail,
  tone = 'default',
  icon,
  className = '',
}: MetricBlockProps) {
  const classes = [
    'metric-block',
    `metric-block--${tone}`,
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <section className={classes}>
      <div className="metric-block__header">
        <p className="metric-block__label">{label}</p>

        {icon && (
          <span className="metric-block__icon" aria-hidden="true">
            {icon}
          </span>
        )}
      </div>

      <p className="metric-block__value">
        <span>{value}</span>
        {unit && <span className="metric-block__unit">{unit}</span>}
      </p>

      {detail && <p className="metric-block__detail">{detail}</p>}
    </section>
  );
}

export default MetricBlock;