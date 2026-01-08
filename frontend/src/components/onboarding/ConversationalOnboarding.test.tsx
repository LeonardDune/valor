import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ConversationalOnboarding } from './ConversationalOnboarding'

// Mock the onComplete and onSkip callbacks
const mockOnComplete = jest.fn()
const mockOnSkip = jest.fn()

const defaultProps = {
  onComplete: mockOnComplete,
  onSkip: mockOnSkip,
}

describe('ConversationalOnboarding', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Initial Render', () => {
    it('renders the welcome message', () => {
      render(<ConversationalOnboarding />)
      expect(screen.getByText('Welcome to VALOR')).toBeInTheDocument()
      expect(screen.getByText('Conversational causal reasoning for policy analysis')).toBeInTheDocument()
    })

    it('renders with proper accessibility attributes', () => {
      render(<ConversationalOnboarding />)
      const heading = screen.getByRole('heading', { level: 1 })
      expect(heading).toHaveTextContent('Welcome to VALOR')
    })
  })

  describe('Conversational Reasoning Explanation', () => {
    it('explains the conversational approach with examples', async () => {
      const user = userEvent.setup()
      render(<ConversationalOnboarding />)

      // Navigate to approach step
      const continueButton = screen.getByRole('button', { name: /continue/i })
      await user.click(continueButton)

      expect(screen.getByText(/conversational approach/i)).toBeInTheDocument()
      expect(screen.getByText(/economic factors.*social pressures/i)).toBeInTheDocument()
    })

    it('includes examples of causal claim articulation', async () => {
      const user = userEvent.setup()
      render(<ConversationalOnboarding />)

      // Navigate to examples step
      const continueButton = screen.getByRole('button', { name: /continue/i })
      await user.click(continueButton) // welcome -> approach
      await user.click(continueButton) // approach -> ai-assistance
      await user.click(continueButton) // ai-assistance -> examples

      expect(screen.getByText(/causal claim/i)).toBeInTheDocument()
      expect(screen.getAllByText(/example/i)).toHaveLength(3) // quick start examples
    })
  })

  describe('AI Assistance Capabilities', () => {
    it('explains AI assistance capabilities', async () => {
      const user = userEvent.setup()
      render(<ConversationalOnboarding />)

      // Navigate to AI assistance step
      const continueButton = screen.getByRole('button', { name: /continue/i })
      await user.click(continueButton) // welcome -> approach
      await user.click(continueButton) // approach -> ai-assistance

      expect(screen.getByText(/AI assistance/i)).toBeInTheDocument()
      expect(screen.getByText(/response times/i)).toBeInTheDocument()
    })

    it('includes response time expectations', async () => {
      const user = userEvent.setup()
      render(<ConversationalOnboarding />)

      // Navigate to AI assistance step
      const continueButton = screen.getByRole('button', { name: /continue/i })
      await user.click(continueButton) // welcome -> approach
      await user.click(continueButton) // approach -> ai-assistance

      expect(screen.getByText(/<3 seconds/i)).toBeInTheDocument()
      expect(screen.getByText(/response time/i)).toBeInTheDocument()
    })
  })

  describe('User Interaction', () => {
    it('allows users to skip the onboarding', async () => {
      const user = userEvent.setup()
      render(<ConversationalOnboarding {...defaultProps} />)

      const skipButton = screen.getByRole('button', { name: /skip/i })
      await user.click(skipButton)

      expect(mockOnSkip).toHaveBeenCalledTimes(1)
    })

    it('allows users to continue through the onboarding', async () => {
      const user = userEvent.setup()
      render(<ConversationalOnboarding {...defaultProps} />)

      // Click through all steps: welcome → approach → ai-assistance → examples → complete
      await user.click(screen.getByRole('button', { name: /continue/i })) // welcome → approach
      await user.click(screen.getByRole('button', { name: /continue/i })) // approach → ai-assistance
      await user.click(screen.getByRole('button', { name: /continue/i })) // ai-assistance → examples
      await user.click(screen.getByRole('button', { name: /complete/i })) // examples → complete (calls onComplete)

      expect(mockOnComplete).toHaveBeenCalledTimes(1)
    })

    it('provides keyboard navigation support', async () => {
      const user = userEvent.setup()
      render(<ConversationalOnboarding {...defaultProps} />)

      // Tab through interactive elements
      await user.tab()
      const firstFocusableElement = document.activeElement

      expect(firstFocusableElement?.tagName).toBe('BUTTON')
    })
  })

  describe('Accessibility (WCAG 2.1 AA)', () => {
    it('has proper heading hierarchy', () => {
      render(<ConversationalOnboarding />)
      const headings = screen.getAllByRole('heading')
      expect(headings).toHaveLength(3) // Main title + 2 section headings
      expect(headings[0]).toHaveAttribute('aria-level', '1')
    })

    it('provides sufficient color contrast', () => {
      render(<ConversationalOnboarding />)
      // This would need visual regression testing, but we can test classes
      const mainHeading = screen.getByRole('heading', { level: 1 })
      expect(mainHeading).toHaveClass('text-gov-900')
    })

    it('supports screen readers with ARIA labels', () => {
      render(<ConversationalOnboarding />)
      // Test will fail until ARIA labels are implemented
      const examples = screen.getAllByLabelText(/causal claim example/i)
      expect(examples).toHaveLength(3)
    })

    it('maintains focus management', async () => {
      const user = userEvent.setup()
      render(<ConversationalOnboarding {...defaultProps} />)

      // Focus should move logically through the interface
      await user.tab()
      await user.tab()
      await user.tab()

      const currentFocus = document.activeElement
      expect(currentFocus).toBeInTheDocument()
    })
  })

  describe('Responsive Design', () => {
    it('adapts to mobile screen sizes', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', { value: 375 })

      render(<ConversationalOnboarding />)
      const container = screen.getByRole('main')
      expect(container).toHaveClass('max-w-2xl')
    })

    it('adapts to tablet screen sizes', () => {
      Object.defineProperty(window, 'innerWidth', { value: 768 })

      render(<ConversationalOnboarding />)
      const container = screen.getByRole('main')
      expect(container).toHaveClass('max-w-2xl')
    })

    it('works on desktop screen sizes', () => {
      Object.defineProperty(window, 'innerWidth', { value: 1024 })

      render(<ConversationalOnboarding />)
      const container = screen.getByRole('main')
      expect(container).toHaveClass('max-w-2xl')
    })
  })

  describe('Performance', () => {
    it('loads within 3 seconds', async () => {
      const startTime = performance.now()

      render(<ConversationalOnboarding />)

      const loadTime = performance.now() - startTime
      expect(loadTime).toBeLessThan(3000) // 3 seconds
    })

    it('renders without layout shifts', () => {
      // This would need visual regression testing
      render(<ConversationalOnboarding />)

      const container = screen.getByRole('main')
      expect(container).toBeInTheDocument()
    })
  })

  describe('Integration Points', () => {
    it('integrates with session management for first-time detection', () => {
      // Test will fail until session integration is implemented
      render(<ConversationalOnboarding />)

      // Should check if this is first session
      expect(screen.getByText(/first time/i)).toBeInTheDocument()
    })

    it('calls onComplete when onboarding is finished', async () => {
      const user = userEvent.setup()
      render(<ConversationalOnboarding {...defaultProps} />)

      // Navigate through all steps: welcome -> approach -> ai-assistance -> examples -> complete
      await user.click(screen.getByRole('button', { name: /continue/i })) // welcome -> approach
      await user.click(screen.getByRole('button', { name: /continue/i })) // approach -> ai-assistance
      await user.click(screen.getByRole('button', { name: /continue/i })) // ai-assistance -> examples

      // Now on examples step, button should be "Complete"
      const completeButton = screen.getByRole('button', { name: /complete/i })
      await user.click(completeButton) // examples -> complete (calls onComplete)

      expect(mockOnComplete).toHaveBeenCalledTimes(1)
    })
  })
})
