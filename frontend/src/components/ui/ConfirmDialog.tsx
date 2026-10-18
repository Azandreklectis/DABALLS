import type { ReactNode } from 'react';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  destructive?: boolean;
  busy?: boolean;
  children?: ReactNode;
  onConfirm: () => void;
  onCancel: () => void;
}

function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  destructive = false,
  busy = false,
  children,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!open) return null;

  return (
    <div
      className="dialog-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !busy) {
          onCancel();
        }
      }}
    >
      <section
        className="confirm-dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        aria-describedby="confirm-dialog-description"
      >
        <p className="confirm-dialog__eyebrow">
          {destructive ? 'ACTION REQUIRED' : 'CONFIRM ACTION'}
        </p>

        <h2
          id="confirm-dialog-title"
          className="confirm-dialog__title"
        >
          {title}
        </h2>

        <p
          id="confirm-dialog-description"
          className="confirm-dialog__description"
        >
          {description}
        </p>

        {children && (
          <div className="confirm-dialog__content">{children}</div>
        )}

        <div className="confirm-dialog__actions">
          <button
            type="button"
            className="button button--secondary button--medium"
            onClick={onCancel}
            disabled={busy}
          >
            {cancelLabel}
          </button>

          <button
            type="button"
            className={
              destructive
                ? 'button button--danger button--medium'
                : 'button button--primary button--medium'
            }
            onClick={onConfirm}
            disabled={busy}
          >
            {busy ? 'Working…' : confirmLabel}
          </button>
        </div>
      </section>
    </div>
  );
}

export default ConfirmDialog;