import type { ReactNode } from 'react';

interface PageHeaderProps {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}

function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: PageHeaderProps) {
  return (
    <section className="page-header">
      <div className="page-header__copy">
        {eyebrow && (
          <p className="page-header__eyebrow">{eyebrow}</p>
        )}

        <h1 className="page-header__title">{title}</h1>

        {description && (
          <p className="page-header__description">{description}</p>
        )}
      </div>

      {actions && <div className="page-header__actions">{actions}</div>}
    </section>
  );
}

export default PageHeader;