'use client';

import { forwardRef, useRef, useEffect, useState, useCallback, type ButtonHTMLAttributes, type InputHTMLAttributes, type TextareaHTMLAttributes, type SelectHTMLAttributes } from 'react';

export const Button = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}>(
  ({ children, className = '', disabled = false, variant = 'primary', size = 'md', 'aria-busy': ariaBusy, ...props }, ref) => (
    <button
      ref={ref}
      className={`
        inline-flex items-center justify-center gap-2 font-medium rounded-lg
        transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2
        disabled:opacity-50 disabled:cursor-not-allowed
        ${className}
        ${size === 'sm' ? 'px-3 py-1.5 text-xs' : size === 'lg' ? 'px-6 py-3 text-base' : 'px-4 py-2.5 text-sm'}
        ${variant === 'primary' ? 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 shadow-sm' : ''}
        ${variant === 'secondary' ? 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-gray-500' : ''}
        ${variant === 'ghost' ? 'bg-transparent text-gray-600 hover:bg-gray-100 hover:text-gray-900 focus:ring-gray-500' : ''}
        ${variant === 'danger' ? 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 shadow-sm' : ''}
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

export const PrimaryButton = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement>>(
  ({ className = '', ...props }, ref) => (
    <Button ref={ref} variant="primary" className={className} {...props} />
  )
);
PrimaryButton.displayName = 'PrimaryButton';

export const SecondaryButton = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement>>(
  ({ className = '', ...props }, ref) => (
    <Button ref={ref} variant="secondary" className={className} {...props} />
  )
);
SecondaryButton.displayName = 'SecondaryButton';

export const GhostButton = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement>>(
  ({ className = '', ...props }, ref) => (
    <Button ref={ref} variant="ghost" className={className} {...props} />
  )
);
GhostButton.displayName = 'GhostButton';

export const DangerButton = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement>>(
  ({ className = '', ...props }, ref) => (
    <Button ref={ref} variant="danger" className={className} {...props} />
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
          <label htmlFor={id} className="label">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={id}
          className={`
            w-full px-4 py-2.5 text-sm border rounded-lg
            transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-0
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
          <p id={hintId} className="hint" role="status">
            {hint}
          </p>
        )}
        {error && (
          <p id={errorId} className="error-text" role="alert" aria-live="polite">
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
          <label htmlFor={id} className="label">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={id}
          rows={rows}
          className={`
            w-full px-4 py-2.5 text-sm border rounded-lg resize-y min-h-[120px]
            transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-0
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
          <p id={hintId} className="hint" role="status">
            {hint}
          </p>
        )}
        {error && (
          <p id={errorId} className="error-text" role="alert" aria-live="polite">
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
          <label htmlFor={id} className="label">
            {label}
          </label>
        )}
        <select
          ref={ref}
          id={id}
          className={`
            w-full px-4 py-2.5 text-sm border rounded-lg appearance-none
            bg-white cursor-pointer
            transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-0
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
          <p id={hintId} className="hint" role="status">
            {hint}
          </p>
        )}
        {error && (
          <p id={errorId} className="error-text" role="alert" aria-live="polite">
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

export function Card({ children, className = '', elevated = false, padding = 'p-6' }: { 
  children: React.ReactNode; 
  className?: string; 
  elevated?: boolean;
  padding?: string;
}) {
  return (
    <div className={`${padding} bg-white border border-gray-200 rounded-xl ${elevated ? 'shadow-lg' : 'shadow-sm hover:shadow-md'} transition-shadow duration-200 ${className}`}>
      {children}
    </div>
  );
}

export function Section({ children, className = '', title, description }: { 
  children: React.ReactNode; 
  className?: string;
  title?: string;
  description?: string;
}) {
  return (
    <section className={className} aria-labelledby={title ? 'section-title' : undefined}>
      {(title || description) && (
        <header className="mb-6">
          {title && <h2 id="section-title" className="text-xl font-semibold text-gray-900">{title}</h2>}
          {description && <p className="mt-1 text-sm text-gray-600">{description}</p>}
        </header>
      )}
      {children}
    </section>
  );
}

export function CopyButton({ text, label = 'Copy' }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  
  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  }, [text]);

  return (
    <button
      type="button"
      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
      onClick={handleCopy}
      aria-label={copied ? 'Copied to clipboard' : label}
    >
      {copied ? (
        <>
          <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
          Copied!
        </>
      ) : (
        <>
          <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z" />
            <path d="M6 3a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2a1 1 0 100 2h2a1 1 0 112 0h2a2 2 0 012 2v8a2 2 0 01-2 2H6a2 2 0 01-2-2V5a2 2 0 012-2h2a1 1 0 100-2H6z" />
          </svg>
          {label}
        </>
      )}
    </button>
  );
}