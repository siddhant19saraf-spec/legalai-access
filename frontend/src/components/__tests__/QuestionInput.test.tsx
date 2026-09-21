import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QuestionInput } from '../QuestionInput';

const mockJurisdictions = [
  { value: 'us_ca', label: 'California' },
  { value: 'us_ny', label: 'New York' },
];

describe('QuestionInput', () => {
  const defaultProps = {
    onSubmit: jest.fn(),
    isLoading: false,
    jurisdictions: mockJurisdictions,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders question textarea', () => {
    render(<QuestionInput {...defaultProps} />);
    expect(screen.getByLabelText('Your Legal Question')).toBeInTheDocument();
  });

  it('renders jurisdiction select', () => {
    render(<QuestionInput {...defaultProps} />);
    expect(screen.getByLabelText('Jurisdiction (Recommended for Accuracy)')).toBeInTheDocument();
  });

  it('submits on form submit', () => {
    render(<QuestionInput {...defaultProps} />);
    const textarea = screen.getByLabelText('Your Legal Question');
    fireEvent.change(textarea, { target: { value: 'Test question' } });
    fireEvent.submit(screen.getByRole('form'));
    expect(defaultProps.onSubmit).toHaveBeenCalledWith('Test question', '', '');
  });

  it('validates minimum question length', () => {
    render(<QuestionInput {...defaultProps} />);
    const textarea = screen.getByLabelText('Your Legal Question');
    fireEvent.change(textarea, { target: { value: 'ab' } });
    fireEvent.submit(screen.getByRole('form'));
    // The error message is in an alert with no accessible name, so query by text
    expect(screen.getByText('Question must be at least 3 characters')).toBeInTheDocument();
    expect(defaultProps.onSubmit).not.toHaveBeenCalled();
  });

  it('validates empty question', () => {
    render(<QuestionInput {...defaultProps} />);
    fireEvent.submit(screen.getByRole('form'));
    expect(screen.getByText('Please enter a legal question')).toBeInTheDocument();
    expect(defaultProps.onSubmit).not.toHaveBeenCalled();
  });

  it('includes jurisdiction in submit', () => {
    render(<QuestionInput {...defaultProps} />);
    const textarea = screen.getByLabelText('Your Legal Question');
    const select = screen.getByLabelText('Jurisdiction (Recommended for Accuracy)');
    fireEvent.change(textarea, { target: { value: 'Test question' } });
    fireEvent.change(select, { target: { value: 'us_ca' } });
    fireEvent.submit(screen.getByRole('form'));
    expect(defaultProps.onSubmit).toHaveBeenCalledWith('Test question', 'us_ca', '');
  });

  it('includes context when expanded', () => {
    render(<QuestionInput {...defaultProps} />);
    const textarea = screen.getByLabelText('Your Legal Question');
    const summary = screen.getByText('Additional Context (Optional)');
    fireEvent.click(summary);
    const contextTextarea = screen.getByLabelText('Additional Details');
    fireEvent.change(textarea, { target: { value: 'Test question' } });
    fireEvent.change(contextTextarea, { target: { value: 'Extra context' } });
    fireEvent.submit(screen.getByRole('form'));
    expect(defaultProps.onSubmit).toHaveBeenCalledWith('Test question', '', 'Extra context');
  });

  it('disables inputs when loading', () => {
    render(<QuestionInput {...defaultProps} isLoading={true} />);
    expect(screen.getByLabelText('Your Legal Question')).toHaveAttribute('disabled');
    expect(screen.getByLabelText('Jurisdiction (Recommended for Accuracy)')).toHaveAttribute('disabled');
    expect(screen.getByRole('button', { name: /analyzing/i })).toHaveAttribute('disabled');
  });

  it('shows loading state on button', () => {
    render(<QuestionInput {...defaultProps} isLoading={true} />);
    expect(screen.getByRole('button', { name: /analyzing/i })).toBeInTheDocument();
  });

  it('displays external error', () => {
    render(<QuestionInput {...defaultProps} error="Server error" />);
    // There are two alerts - check for the external error div with assertive live region (the div, not the p)
    const externalErrorDiv = screen.getAllByText('Server error').find(el => 
      el.tagName === 'DIV' && el.getAttribute('role') === 'alert' && el.getAttribute('aria-live') === 'assertive'
    );
    expect(externalErrorDiv).toBeInTheDocument();
  });

  it('clears validation error on input change', () => {
    render(<QuestionInput {...defaultProps} error="Server error" />);
    const textarea = screen.getByLabelText('Your Legal Question');
    // First trigger a validation error
    fireEvent.change(textarea, { target: { value: 'ab' } });
    fireEvent.submit(screen.getByRole('form'));
    expect(screen.getByText('Question must be at least 3 characters')).toBeInTheDocument();
    // Now fix the input - validation error should clear
    fireEvent.change(textarea, { target: { value: 'Valid question' } });
    expect(screen.queryByText('Question must be at least 3 characters')).not.toBeInTheDocument();
    // External error should still be there (the div with assertive live region)
    const externalErrorDiv = screen.getAllByText('Server error').find(el => 
      el.tagName === 'DIV' && el.getAttribute('role') === 'alert' && el.getAttribute('aria-live') === 'assertive'
    );
    expect(externalErrorDiv).toBeInTheDocument();
  });
});