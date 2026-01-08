import React, { useState, useCallback, useRef } from 'react'

interface CausalClaim {
  id: string
  text: string
  timestamp: Date
  userId: string
  confidence: number
  isValid: boolean
  validationErrors: string[]
  suggestions: string[]
}

interface CausalClaimInputProps {
  onClaimSubmit?: (claim: CausalClaim) => void
  onValidationChange?: (isValid: boolean, errors: string[]) => void
  placeholder?: string
  maxLength?: number
  userId?: string
}

export function CausalClaimInput({
  onClaimSubmit,
  onValidationChange,
  placeholder = "Enter a causal claim (e.g., 'Economic pressure increases when unemployment rises')",
  maxLength = 500,
  userId = "user-1"
}: CausalClaimInputProps) {
  const [inputValue, setInputValue] = useState('')
  const [isValidating, setIsValidating] = useState(false)
  const [validationResult, setValidationResult] = useState<{
    isValid: boolean
    errors: string[]
    suggestions: string[]
  }>({ isValid: true, errors: [], suggestions: [] })

  const validateCausalClaim = useCallback((text: string) => {
    const errors: string[] = []
    const suggestions: string[] = []

    if (!text.trim()) {
      return { isValid: true, errors: [], suggestions: [] }
    }

    // Check for causal keywords
    const hasCausalKeywords = /\b(increases?|decreases?|rises?|falls?|grows?|declines?|improves?|worsens?)\b.*\bwhen\b/i.test(text)

    if (!hasCausalKeywords) {
      errors.push("Causal claims should describe how one factor changes when another changes")
      suggestions.push("Try using words like 'increases', 'decreases', 'rises', or 'falls' followed by 'when'")
      suggestions.push("Example: 'Economic pressure increases when unemployment rises'")
    }

    // Check for causal direction indicators
    const hasDirectionIndicators = /\b(when|because|due to|leads to|results in|causes?|affects?)\b/i.test(text)

    if (!hasDirectionIndicators) {
      suggestions.push("Consider using words like 'when', 'because', 'leads to', or 'causes'")
    }

    // Check minimum length for meaningful claims
    if (text.trim().length < 10) {
      errors.push("Causal claims should be more descriptive")
      suggestions.push("Provide more context about the relationship between factors")
    }

    // Check for proper structure (subject-verb-object pattern)
    const hasProperStructure = /\w+.*\w+.*\w+/.test(text.trim())

    if (!hasProperStructure) {
      errors.push("Causal claims need both a cause and effect")
    }

    return {
      isValid: errors.length === 0,
      errors,
      suggestions
    }
  }, [])

  const validationTimeoutRef = useRef<NodeJS.Timeout>()

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    setInputValue(value)

    // Clear existing timeout
    if (validationTimeoutRef.current) {
      clearTimeout(validationTimeoutRef.current)
    }

    // Debounced validation
    setIsValidating(true)
    validationTimeoutRef.current = setTimeout(() => {
      const result = validateCausalClaim(value)
      setValidationResult(result)
      onValidationChange?.(result.isValid, result.errors)
      setIsValidating(false)
    }, 300)
  }, [validateCausalClaim, onValidationChange])

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault()

    if (!inputValue.trim() || !validationResult.isValid) {
      return
    }

    const claim: CausalClaim = {
      id: `claim-${Date.now()}`,
      text: inputValue.trim(),
      timestamp: new Date(),
      userId,
      confidence: 0.8, // Default confidence, could be calculated based on validation
      isValid: validationResult.isValid,
      validationErrors: validationResult.errors,
      suggestions: validationResult.suggestions
    }

    onClaimSubmit?.(claim)
    setInputValue('')
    setValidationResult({ isValid: true, errors: [], suggestions: [] })
  }, [inputValue, validationResult, userId, onClaimSubmit])

  return (
    <div className="card max-w-2xl w-full">
      <h3 className="text-lg font-semibold text-gov-900 mb-4">
        Enter Causal Claim
      </h3>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="causal-claim-input" className="block text-sm font-medium text-gov-700 mb-2">
            Causal Relationship
          </label>
          <textarea
            id="causal-claim-input"
            value={inputValue}
            onChange={handleInputChange}
            placeholder={placeholder}
            maxLength={maxLength}
            rows={3}
            className="input-field resize-none"
            aria-describedby="input-help validation-feedback"
            aria-invalid={!validationResult.isValid}
          />
          <div id="input-help" className="text-sm text-gov-600 mt-1">
            Describe how one factor changes when another changes. Use natural language.
          </div>
        </div>

        {/* Validation Feedback */}
        {isValidating && (
          <div className="text-sm text-gov-600" aria-live="polite">
            Validating...
          </div>
        )}

        {!validationResult.isValid && validationResult.errors.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4" role="alert">
            <h4 className="text-sm font-medium text-red-800 mb-2">Validation Issues:</h4>
            <ul className="text-sm text-red-700 space-y-1">
              {validationResult.errors.map((error, index) => (
                <li key={index}>• {error}</li>
              ))}
            </ul>
          </div>
        )}

        {validationResult.suggestions.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-blue-800 mb-2">Suggestions:</h4>
            <ul className="text-sm text-blue-700 space-y-1">
              {validationResult.suggestions.map((suggestion, index) => (
                <li key={index}>• {suggestion}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex justify-end space-x-3">
          <button
            type="submit"
            disabled={!inputValue.trim() || !validationResult.isValid || isValidating}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            aria-describedby="submit-help"
          >
            Submit Claim
          </button>
        </div>
        <div id="submit-help" className="sr-only">
          Submit the causal claim for processing and storage
        </div>
      </form>
    </div>
  )
}