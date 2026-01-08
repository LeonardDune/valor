import React, { useState } from 'react'

interface ConversationalOnboardingProps {
  onComplete?: () => void
  onSkip?: () => void
}

type OnboardingStep = 'welcome' | 'approach' | 'ai-assistance' | 'examples' | 'complete'

export function ConversationalOnboarding({ onComplete, onSkip }: ConversationalOnboardingProps) {
  const [currentStep, setCurrentStep] = useState<OnboardingStep>('welcome')

  const handleContinue = () => {
    switch (currentStep) {
      case 'welcome':
        setCurrentStep('approach')
        break
      case 'approach':
        setCurrentStep('ai-assistance')
        break
      case 'ai-assistance':
        setCurrentStep('examples')
        break
      case 'examples':
        setCurrentStep('complete')
        onComplete?.()
        break
      default:
        break
    }
  }

  const handleSkip = () => {
    onSkip?.()
  }

  const renderWelcomeStep = () => (
    <>
      <h1 className="text-2xl font-bold text-gov-900 mb-4">
        Welcome to VALOR
      </h1>
      <p className="text-gov-700 mb-6">
        Conversational causal reasoning for policy analysis
      </p>
      <p className="text-gov-600 mb-6">
        Get started with understanding how to articulate and explore causal relationships in policy contexts.
      </p>
    </>
  )

  const renderApproachStep = () => (
    <>
      <h2 className="text-xl font-semibold text-gov-900 mb-4">
        Conversational Approach
      </h2>
      <p className="text-gov-700 mb-4">
        VALOR uses a conversational approach to causal reasoning. Instead of building complex diagrams upfront,
        you can articulate causal claims naturally, like:
      </p>
      <div className="bg-gov-50 p-4 rounded-lg mb-6">
        <p className="text-gov-800 italic">
          "Economic factors increase when social pressures rise"
        </p>
      </div>
      <p className="text-gov-700 mb-6">
        This natural language approach makes causal reasoning more accessible and collaborative.
      </p>
    </>
  )

  const renderAIAssistanceStep = () => (
    <>
      <h2 className="text-xl font-semibold text-gov-900 mb-4">
        AI Assistance & Response Times
      </h2>
      <p className="text-gov-700 mb-4">
        VALOR provides AI assistance to help you:
      </p>
      <ul className="list-disc list-inside text-gov-700 mb-6 space-y-2">
        <li>Suggest related causal factors</li>
        <li>Identify potential conflicts in your reasoning</li>
        <li>Explore alternative explanations</li>
        <li>Validate causal relationships</li>
      </ul>
      <div className="bg-blue-50 p-4 rounded-lg mb-6">
        <p className="text-blue-800">
          <strong>Response Time:</strong> AI responses typically arrive in under 3 seconds
        </p>
      </div>
    </>
  )

  const renderExamplesStep = () => (
    <>
      <h2 className="text-xl font-semibold text-gov-900 mb-4">
        Quick Start Examples
      </h2>
      <p className="text-gov-700 mb-4">
        Here are some examples of causal claim articulation:
      </p>
      <div className="space-y-4 mb-6">
        <div className="border border-gov-200 p-4 rounded-lg" aria-label="Causal claim example 1">
          <p className="font-medium text-gov-900 mb-2">Policy Impact Example</p>
          <p className="text-gov-700">"Tax incentives decrease when unemployment rates rise"</p>
        </div>
        <div className="border border-gov-200 p-4 rounded-lg" aria-label="Causal claim example 2">
          <p className="font-medium text-gov-900 mb-2">Social Dynamics Example</p>
          <p className="text-gov-700">"Community engagement increases when local participation opportunities expand"</p>
        </div>
        <div className="border border-gov-200 p-4 rounded-lg" aria-label="Causal claim example 3">
          <p className="font-medium text-gov-900 mb-2">Environmental Policy Example</p>
          <p className="text-gov-700">"Carbon emissions decrease when renewable energy adoption accelerates"</p>
        </div>
      </div>
    </>
  )

  const renderCompleteStep = () => (
    <>
      <h2 className="text-xl font-semibold text-gov-900 mb-4">
        Ready to Start!
      </h2>
      <p className="text-gov-700 mb-6">
        You're now ready to begin exploring causal relationships in VALOR.
        Remember to articulate your claims conversationally and leverage AI assistance for deeper insights.
      </p>
      <div className="bg-green-50 p-4 rounded-lg mb-6">
        <p className="text-green-800">
          ✅ Onboarding complete! Welcome to conversational causal reasoning.
        </p>
      </div>
    </>
  )

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 'welcome':
        return renderWelcomeStep()
      case 'approach':
        return renderApproachStep()
      case 'ai-assistance':
        return renderAIAssistanceStep()
      case 'examples':
        return renderExamplesStep()
      case 'complete':
        return renderCompleteStep()
      default:
        return renderWelcomeStep()
    }
  }

  const getStepIndicator = () => {
    const steps = ['welcome', 'approach', 'ai-assistance', 'examples', 'complete'] as const
    const currentIndex = steps.indexOf(currentStep)

    return (
      <div className="flex justify-center mb-6" role="progressbar" aria-valuenow={currentIndex + 1} aria-valuemax={5}>
        {steps.map((step, index) => (
          <div
            key={step}
            className={`w-3 h-3 rounded-full mx-1 ${
              index <= currentIndex ? 'bg-valor-primary' : 'bg-gov-300'
            }`}
            aria-label={`Step ${index + 1} of 5${index <= currentIndex ? ' - completed' : ''}`}
          />
        ))}
      </div>
    )
  }

  return (
    <main className="card max-w-2xl w-full" role="main" aria-labelledby="onboarding-title">
      {getStepIndicator()}
      {renderCurrentStep()}

      <div className="flex justify-between mt-8">
        <button
          onClick={handleSkip}
          className="btn-secondary"
          aria-label="Skip onboarding and go directly to VALOR"
        >
          Skip
        </button>
        <button
          onClick={handleContinue}
          className="btn-primary"
          aria-label={currentStep === 'complete' ? 'Finish onboarding' : currentStep === 'examples' ? 'Complete onboarding' : 'Continue to next step'}
        >
          {currentStep === 'complete' ? 'Get Started' : currentStep === 'examples' ? 'Complete' : 'Continue'}
        </button>
      </div>

      {/* Screen reader announcements for step changes */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {currentStep === 'complete' ? 'Onboarding completed successfully' : `Step ${['welcome', 'approach', 'ai-assistance', 'examples', 'complete'].indexOf(currentStep) + 1} of 5`}
      </div>
    </main>
  )
}
