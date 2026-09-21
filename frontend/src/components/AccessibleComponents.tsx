'use client';

import { forwardRef, useRef, useEffect, type ButtonHTMLAttributes, type InputHTMLAttributes, type TextareaHTMLAttributes, type SelectHTMLAttributes } from 'react';

export const Button = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}>(
  ({ children, className = '', disabled = false, variant = 'md', 'aria-busy': ariaBusy, ...props }, ref) => (
    <button
      ref={ref}
      className={`
        inline-flex items-center justify-center px-4 py-2.5 text-sm font-medium rounded-lg
        transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2
        disabled:opacity-50 disabled:cursor-not-allowed
        ${className}
        ${variant === 'sm' ? 'text-sm py-1' : variant === 'lg' ? 'text-base py-3' : ''}
      `}
      disabled={disabled}
      aria-busy={ariaBusy}
      {...props}
    >
      {children}
    </button>
  )
);
Button.displayName = 'Button';

export const PrimaryButton = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' }>(
  ({ className = '', variant = 'primary', ...props }, ref) => (
    <Button
      ref={ref}
      variant={variant}
      className={`
        bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500
        ${className}
      `}
      {...props}
    />
  )
);
PrimaryButton.displayName = 'PrimaryButton';

export const SecondaryButton = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'secondary' }>(
  ({ className = '', variant = 'secondary', ...props }, ref) => (
    <Button
      ref={ref}
      variant={variant}
      className={`
        bg-gray-100 text-gray-900 hover:bg-gray-200 focus:ring-gray-500
        border border-gray-300
        ${className}
      `}
      {...props}
    />
  )
);
SecondaryButton.displayName = 'SecondaryButton';

export const DangerButton = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'danger' }>(
  ({ className = '', ...props }, ref) => (
    <Button
ref={ref}
      variant="danger"
      className={`
        bg-red-600 text-white hover:bg-red-700 focus:ring-red-500
      `}
      {...props}
    />
  )
);
DangerButton.displayName = 'DangerButton';

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  error?: string;
  hint?: string;
}>(
  ({ label, error, hint, id, className = '', 'aria-describedby': ariaDescribedBy, ...props }, ref) => {
    const errorId = error ? `${id}-error` : undefined;
    const hintId = hint ? `${id}-hint` : undefined;
    const describedBy = [errorId, hintId, ariaDescribedBy].filter(Boolean).join(' ') || undefined;

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1.5">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={id}
          className={`
            w-full px-3 py-2 text-sm border rounded-lg
            transition-colors focus:outline-none focus:ring-2 focus:ring-offset-0
            ${error
              ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
              : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'
            }
            ${className}
          `}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={describedBy}
          aria-errormessage={errorId}
          {...props}
        />
        {hint && !error && (
          <p id={hintId} className="mt-1.5 text-sm text-gray-500" role="status">
            {hint}
          </p>
        )}
        {error && (
          <p id={errorId} className="mt-1.5 text-sm text-red-600" role="alert" aria-live="polite">
            {error}
          </p>
        )}
      </div>
    );
  }
);
Input.displayName = 'Input';

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement> & {
  label?: string;
  error?: string;
  hint?: string;
}>(
  ({ label, error, hint, id, className = '', rows = 4, 'aria-describedby': ariaDescribedBy, ...props }, ref) => {
    const errorId = error ? `${id}-error` : undefined;
    const hintId = hint ? `${id}-hint` : undefined;
    const describedBy = [errorId, hintId, ariaDescribedBy].filter(Boolean).join(' ') || undefined;

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1.5">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={id}
          rows={rows}
          className={`
            w-full px-3 py-2 text-sm border rounded-lg resize-y min-h-[100px]
            transition-colors focus:outline-none focus:ring-2 focus:ring-offset-0
            ${error
              ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
              : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'
            }
            ${className}
          `}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={describedBy}
          aria-errormessage={errorId}
          {...props}
        />
        {hint && !error && (
          <p id={hintId} className="mt-1.5 text-sm text-gray-500" role="status">
            {hint}
          </p>
        )}
        {error && (
          <p id={errorId} className="mt-1.5 text-sm text-red-600" role="alert" aria-live="polite">
            {error}
          </p>
        )}
      </div>
    );
  }
);
Textarea.displayName = 'Textarea';

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement> & {
  label?: string;
  error?: string;
  hint?: string;
  options: { value: string; label: string }[];
  placeholder?: string;
}>(
  ({ label, error, hint, id, className = '', options, placeholder, 'aria-describedby': ariaDescribedBy, ...props }, ref) => {
    const errorId = error ? `${id}-error` : undefined;
    const hintId = hint ? `${id}-hint` : undefined;
    const describedBy = [errorId, hintId, ariaDescribedBy].filter(Boolean).join(' ') || undefined;

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1.5">
            {label}
          </label>
        )}
        <select
          ref={ref}
          id={id}
          className={`
            w-full px-3 py-2 text-sm border rounded-lg appearance-none
            bg-white cursor-pointer
            transition-colors focus:outline-none focus:ring-2 focus:ring-offset-0
            ${error
              ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
              : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'
            }
            ${className}
          `}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={describedBy}
          aria-errormessage={errorId}
          {...props}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        {hint && !error && (
          <p id={hintId} className="mt-1.5 text-sm text-gray-500" role="status">
            {hint}
          </p>
        )}
        {error && (
          <p id={errorId} className="mt-1.5 text-sm text-red-600" role="alert" aria-live="polite">
            {error}
          </p>
        )}
      </div>
    );
  }
);
Select.displayName = 'Select';

export function VisuallyHidden({ children }: { children: React.ReactNode }) {
  return (
    <span
      style={{
        position: 'absolute',
        width: '1px',
        height: '1px',
        padding: 0,
        margin: '-1px',
        overflow: 'hidden',
        clip: 'rect(0, 0, 0, 0)',
        whiteSpace: 'nowrap',
        border: 0,
      }}
      aria-hidden="true"
    >
      {children}
    </span>
  );
}

export function FocusTrap({ children, active = true }: { children: React.ReactNode; active?: boolean }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!active || !containerRef.current) return;

    previousActiveElement.current = document.activeElement as HTMLElement;
    containerRef.current.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      const focusableElements = containerRef.current?.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );

      if (!focusableElements?.length) return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      previousActiveElement.current?.focus();
    };
  }, [active]);

  return (
    <div
      ref={containerRef}
      tabIndex={-1}
      style={{ outline: 'none' }}
    >
      {children}
    </div>
  );
}

