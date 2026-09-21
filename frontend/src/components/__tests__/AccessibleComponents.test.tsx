import { render, screen, fireEvent } from '@testing-library/react';
import { Button, PrimaryButton, Input, Textarea, Select, VisuallyHidden } from '../AccessibleComponents';

describe('AccessibleComponents', () => {
  describe('Button', () => {
    it('renders children', () => {
      render(<Button>Click me</Button>);
      expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
    });

    it('applies disabled state', () => {
      render(<Button disabled>Click me</Button>);
      const button = screen.getByRole('button', { name: 'Click me' });
      expect(button).toHaveAttribute('disabled');
      // aria-busy should not be present when not provided
      expect(button).not.toHaveAttribute('aria-busy');
    });

    it('sets aria-busy when provided', () => {
      render(<Button aria-busy={true}>Loading</Button>);
      expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'true');
    });

    it('forwards ref', () => {
      const ref = jest.fn();
      render(<Button ref={ref}>Test</Button>);
      expect(ref).toHaveBeenCalledWith(expect.any(HTMLButtonElement));
    });
  });

  describe('PrimaryButton', () => {
    it('renders with primary styling', () => {
      render(<PrimaryButton>Primary</PrimaryButton>);
      const button = screen.getByRole('button', { name: 'Primary' });
      expect(button).toHaveClass('bg-blue-600');
      expect(button).toHaveClass('text-white');
    });
  });

  describe('Input', () => {
    it('renders label and input', () => {
      render(<Input id="test" label="Test Label" />);
      expect(screen.getByLabelText('Test Label')).toBeInTheDocument();
    });

    it('shows error message', () => {
      render(<Input id="test" label="Test" error="This is an error" />);
      expect(screen.getByRole('alert')).toHaveTextContent('This is an error');
      expect(screen.getByLabelText('Test')).toHaveAttribute('aria-invalid', 'true');
    });

    it('shows hint', () => {
      render(<Input id="test" label="Test" hint="Helper text" />);
      expect(screen.getByText('Helper text')).toBeInTheDocument();
    });

    it('associates error with input via aria-errormessage', () => {
      render(<Input id="test" label="Test" error="Error" />);
      const input = screen.getByLabelText('Test');
      expect(input).toHaveAttribute('aria-errormessage');
    });
  });

  describe('Textarea', () => {
    it('renders with correct rows', () => {
      render(<Textarea id="test" label="Test" rows={5} />);
      expect(screen.getByLabelText('Test')).toHaveAttribute('rows', '5');
    });

    it('shows error', () => {
      render(<Textarea id="test" label="Test" error="Error" />);
      expect(screen.getByRole('alert')).toHaveTextContent('Error');
    });
  });

  describe('Select', () => {
    it('renders options', () => {
      render(
        <Select
          id="test"
          label="Test"
          options={[
            { value: 'a', label: 'Option A' },
            { value: 'b', label: 'Option B' },
          ]}
        />
      );
      expect(screen.getByRole('combobox')).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Option A' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Option B' })).toBeInTheDocument();
    });

    it('shows placeholder', () => {
      render(
        <Select
          id="test"
          label="Test"
          placeholder="Choose..."
          options={[]}
        />
      );
      expect(screen.getByRole('combobox')).toHaveTextContent('Choose...');
    });

    it('shows error', () => {
      render(
        <Select
          id="test"
          label="Test"
          error="Required"
          options={[]}
        />
      );
      expect(screen.getByRole('alert')).toHaveTextContent('Required');
    });
  });

  describe('VisuallyHidden', () => {
    it('hides content visually but keeps accessible', () => {
      render(<VisuallyHidden>Hidden text</VisuallyHidden>);
      const element = screen.getByText('Hidden text');
      expect(element).toHaveStyle({
        position: 'absolute',
        width: '1px',
        height: '1px',
      });
    });
  });
});