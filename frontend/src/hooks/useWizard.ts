import { useState, useCallback } from 'react';

interface UseWizardOptions<T> {
  totalSteps: number;
  initialData: T;
  onComplete?: (data: T) => void;
}

interface UseWizardReturn<T> {
  currentStep: number;
  formData: T;
  totalSteps: number;
  isFirstStep: boolean;
  isLastStep: boolean;
  next: () => void;
  back: () => void;
  goToStep: (step: number) => void;
  setData: (partial: Partial<T>) => void;
  reset: () => void;
}

export function useWizard<T extends object>({
  totalSteps,
  initialData,
  onComplete,
}: UseWizardOptions<T>): UseWizardReturn<T> {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState<T>(initialData);

  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === totalSteps - 1;

  const next = useCallback(() => {
    if (isLastStep) {
      onComplete?.(formData);
    } else {
      setCurrentStep((s) => Math.min(s + 1, totalSteps - 1));
    }
  }, [isLastStep, formData, onComplete, totalSteps]);

  const back = useCallback(() => {
    setCurrentStep((s) => Math.max(s - 1, 0));
  }, []);

  const goToStep = useCallback(
    (step: number) => {
      if (step >= 0 && step < totalSteps) {
        setCurrentStep(step);
      }
    },
    [totalSteps]
  );

  const setData = useCallback((partial: Partial<T>) => {
    setFormData((prev) => ({ ...prev, ...partial }));
  }, []);

  const reset = useCallback(() => {
    setCurrentStep(0);
    setFormData(initialData);
  }, [initialData]);

  return {
    currentStep,
    formData,
    totalSteps,
    isFirstStep,
    isLastStep,
    next,
    back,
    goToStep,
    setData,
    reset,
  };
}
