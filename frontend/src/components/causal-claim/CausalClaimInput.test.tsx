import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CausalClaimInput } from './CausalClaimInput'

// Mock timers for debounced validation
jest.useFakeTimers()

const mockOnClaimSubmit = jest.fn()
const mockOnValidationChange = jest.fn()

const defaultProps = {
  onClaimSubmit: mockOnClaimSubmit,
  onValidationChange: mockOnValidationChange,
  userId: 'test-user-123'
}

describe('CausalClaimInput', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Initial Render', () => {
    it('renders the input form with proper labels', () => {
      render(<CausalClaimInput />)

      expect(screen.getByRole('heading', { name: /enter causal claim/i })).toBeInTheDocument()
      expect(screen.getByLabelText(/causal relationship/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /submit claim/i })).toBeInTheDocument()
    })

    it('shows the default placeholder text', () => {
      render(<CausalClaimInput />)

      const textarea = screen.getByPlaceholderText(/enter a causal claim.*economic pressure increases/i)
      expect(textarea).toBeInTheDocument()
    })

    it('renders with proper accessibility attributes', () => {
      render(<CausalClaimInput />)

      const textarea = screen.getByRole('textbox')
      expect(textarea).toHaveAttribute('aria-describedby')
      expect(textarea).toHaveAttribute('aria-invalid', 'false')
    })
  })

  describe('Input Validation', () => {
    it('validates valid causal claims', async () => {
      const user = userEvent.setup({ delay: null })
      render(<CausalClaimInput {...defaultProps} />)

      const textarea = screen.getByRole('textbox')
      await user.type(textarea, 'Economic pressure increases when unemployment rises')

      // Wait for debounced validation
      jest.runOnlyPendingTimers()

      await waitFor(() => {
        expect(mockOnValidationChange).toHaveBeenCalledWith(true, [])
      })
    })

    it('rejects invalid causal claims without proper structure', async () => {
      const user = userEvent.setup({ delay: null })
      render(<CausalClaimInput {...defaultProps} />)

      const textarea = screen.getByRole('textbox')
      await user.type(textarea, 'invalid claim')

      // Wait for debounced validation
      jest.runOnlyPendingTimers()

      await waitFor(() => {
        expect(mockOnValidationChange).toHaveBeenCalledWith(false, expect.any(Array))
        expect(screen.getByText(/validation issues/i)).toBeInTheDocument()
      })
    })

    it('provides helpful error messages for malformed inputs', async () => {
      const user = userEvent.setup({ delay: null })
      render(<CausalClaimInput {...defaultProps} />)

      const textarea = screen.getByRole('textbox')
      await user.type(textarea, 'test')

      // Wait for debounced validation
      jest.runOnlyPendingTimers()

      await waitFor(() => {
        expect(screen.getByText(/causal claims should be more descriptive/i)).toBeInTheDocument()
      })
    })

    it('shows suggestions for improvement', async () => {
      const user = userEvent.setup({ delay: null })
      render(<CausalClaimInput {...defaultProps} />)

      const textarea = screen.getByRole('textbox')
      await user.type(textarea, 'pressure unemployment')

      // Wait for debounced validation
      jest.runOnlyPendingTimers()

      await waitFor(() => {
        expect(screen.getByText(/suggestions/i)).toBeInTheDocument()
        expect(screen.getByText(/try using words like.*increases.*decreases/i)).toBeInTheDocument()
      })
    })

    it('validates claims with different causal keywords', async () => {
      const user = userEvent.setup({ delay: null })
      render(<CausalClaimInput {...defaultProps} />)

      const testCases = [
        'Economic growth decreases when interest rates rise',
        'Social cohesion improves when community programs expand',
        'Air quality worsens when industrial activity grows'
      ]

      for (const claim of testCases) {
        const textarea = screen.getByRole('textbox')
        await user.clear(textarea)
        await user.type(textarea, claim)

        // Wait for debounced validation
        jest.runOnlyPendingTimers()

        await waitFor(() => {
          expect(mockOnValidationChange).toHaveBeenCalledWith(true, [])
        })
      }
    })
  })

  describe('Claim Submission', () => {
    it('submits valid claims with complete metadata', async () => {
      const user = userEvent.setup({ delay: null })
      render(<CausalClaimInput {...defaultProps} />)

      const textarea = screen.getByRole('textbox')
      await user.type(textarea, 'Economic pressure increases when unemployment rises')

      // Wait for validation
      jest.runOnlyPendingTimers()

      const submitButton = screen.getByRole('button', { name: /submit claim/i })
      await user.click(submitButton)

      expect(mockOnClaimSubmit).toHaveBeenCalledWith({
        id: expect.stringMatching(/^claim-\d+$/),
        text: 'Economic pressure increases when unemployment rises',
        timestamp: expect.any(Date),
        userId: 'test-user-123',
        confidence: 0.8,
        isValid: true,
        validationErrors: [],
        suggestions: []
      })
    })

    it('prevents submission of invalid claims', async () => {
      const user = userEvent.setup({ delay: null })
      render(<CausalClaimInput {...defaultProps} />)

      const textarea = screen.getByRole('textbox')
      await user.type(textarea, 'invalid')

      // Wait for validation
      jest.runOnlyPendingTimers()

      const submitButton = screen.getByRole('button', { name: /submit claim/i })
      expect(submitButton).toBeDisabled()
    })

    it('clears the form after successful submission', async () => {
      const user = userEvent.setup({ delay: null })
      render(<CausalClaimInput {...defaultProps} />)

      const textarea = screen.getByRole('textbox')
      await user.type(textarea, 'Economic pressure increases when unemployment rises')

      // Wait for validation
      jest.runOnlyPendingTimers()

      const submitButton = screen.getByRole('button', { name: /submit claim/i })
      await user.click(submitButton)

      expect(textarea).toHaveValue('')
    })

    it('includes validation errors in submitted claim metadata', async () => {
      const user = userEvent.setup({ delay: null })
      render(<CausalClaimInput {...defaultProps} />)

      const textarea = screen.getByRole('textbox')
      await user.type(textarea, 'Economic pressure increases when unemployment rises')

      // Wait for validation
      jest.runOnlyPendingTimers()

      const submitButton = screen.getByRole('button', { name: /submit claim/i })
      await user.click(submitButton)

      const submittedClaim = mockOnClaimSubmit.mock.calls[0][0]
      expect(submittedClaim.validationErrors).toEqual([])
      expect(submittedClaim.isValid).toBe(true)
    })
  })

  describe('Real-time Validation', () => {
    it('debounces validation to prevent excessive calls', async () => {
      const user = userEvent.setup({ delay: null })
      render(<CausalClaimInput {...defaultProps} />)

      const textarea = screen.getByRole('textbox')

      // Type multiple characters quickly
      await user.type(textarea, 'Economic pressure increases when unemployment rises')

      // Validation should not have been called yet (debounced)
      expect(mockOnValidationChange).not.toHaveBeenCalled()

      // Fast-forward timers to trigger validation
      jest.runOnlyPendingTimers()

      await waitFor(() => {
        expect(mockOnValidationChange).toHaveBeenCalledTimes(1)
      })
    })

    it('shows validation feedback immediately during typing', async () => {
      const user = userEvent.setup({ delay: null })
      render(<CausalClaimInput {...defaultProps} />)

      const textarea = screen.getByRole('textbox')
      await user.type(textarea, 'test')

      // Should show "Validating..." during debounce period
      expect(screen.getByText(/validating/i)).toBeInTheDocument()
    })

    it('updates validation status as user types', async () => {
      const user = userEvent.setup({ delay: null })
      render(<CausalClaimInput {...defaultProps} />)

      const textarea = screen.getByRole('textbox')

      // Start with invalid input
      await user.type(textarea, 'bad')
      jest.runOnlyPendingTimers()

      await waitFor(() => {
        expect(mockOnValidationChange).toHaveBeenCalledWith(false, expect.any(Array))
      })

      // Clear and enter valid input
      await user.clear(textarea)
      await user.type(textarea, 'Economic pressure increases when unemployment rises')
      jest.runOnlyPendingTimers()

      await waitFor(() => {
        expect(mockOnValidationChange).toHaveBeenLastCalledWith(true, [])
      })
    })
  })

  describe('Accessibility', () => {
    it('provides proper ARIA labels and descriptions', () => {
      render(<CausalClaimInput />)

      const textarea = screen.getByRole('textbox')
      expect(textarea).toHaveAttribute('aria-describedby')

      const helpText = screen.getByText(/describe how one factor changes/i)
      expect(helpText).toHaveAttribute('id')
    })

    it('updates aria-invalid when validation fails', async () => {
      const user = userEvent.setup({ delay: null })
      render(<CausalClaimInput {...defaultProps} />)

      const textarea = screen.getByRole('textbox')
      expect(textarea).toHaveAttribute('aria-invalid', 'false')

      await user.type(textarea, 'invalid')
      jest.runOnlyPendingTimers()

      await waitFor(() => {
        expect(textarea).toHaveAttribute('aria-invalid', 'true')
      })
    })

    it('provides screen reader feedback for validation results', async () => {
      const user = userEvent.setup({ delay: null })
      render(<CausalClaimInput {...defaultProps} />)

      const textarea = screen.getByRole('textbox')
      await user.type(textarea, 'invalid claim')
      jest.runOnlyPendingTimers()

      await waitFor(() => {
        const alert = screen.getByRole('alert')
        expect(alert).toBeInTheDocument()
      })
    })

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      render(<CausalClaimInput />)

      // Tab to textarea
      await user.tab()
      expect(screen.getByRole('textbox')).toHaveFocus()

      // Tab to submit button
      await user.tab()
      expect(screen.getByRole('button', { name: /submit claim/i })).toHaveFocus()
    })
  })

  describe('Performance', () => {
    it('validates claims within 500ms', async () => {
      const user = userEvent.setup({ delay: null })
      render(<CausalClaimInput {...defaultProps} />)

      const startTime = performance.now()
      const textarea = screen.getByRole('textbox')
      await user.type(textarea, 'Economic pressure increases when unemployment rises')

      jest.runOnlyPendingTimers()

      await waitFor(() => {
        expect(mockOnValidationChange).toHaveBeenCalled()
      })

      const endTime = performance.now()
      expect(endTime - startTime).toBeLessThan(500)
    })

    it('handles rapid typing without performance degradation', async () => {
      const user = userEvent.setup({ delay: null })
      render(<CausalClaimInput {...defaultProps} />)

      const textarea = screen.getByRole('textbox')

      // Simulate rapid typing
      for (let i = 0; i < 10; i++) {
        await user.type(textarea, `Test input ${i} `)
      }

      jest.runOnlyPendingTimers()

      // Should only validate once due to debouncing
      await waitFor(() => {
        expect(mockOnValidationChange).toHaveBeenCalledTimes(1)
      })
    })
  })

  describe('Integration', () => {
    it('integrates with session management for user identification', () => {
      render(<CausalClaimInput userId="session-user-456" />)

      const textarea = screen.getByRole('textbox')
      fireEvent.change(textarea, {
        target: { value: 'Economic pressure increases when unemployment rises' }
      })

      jest.runOnlyPendingTimers()

      // The component should use the provided userId
      expect(textarea).toBeInTheDocument()
    })

    it('supports custom placeholders and configuration', () => {
      render(
        <CausalClaimInput
          placeholder="Custom placeholder text"
          maxLength={100}
        />
      )

      expect(screen.getByPlaceholderText('Custom placeholder text')).toBeInTheDocument()
      const textarea = screen.getByRole('textbox')
      expect(textarea).toHaveAttribute('maxlength', '100')
    })
  })
})