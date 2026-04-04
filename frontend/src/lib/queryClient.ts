import { QueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { AxiosError } from 'axios';

interface ApiErrorResponse {
  message?: string;
  detail?: string;
}

function handleQueryError(error: unknown): void {
  if (error instanceof AxiosError) {
    const data = error.response?.data as ApiErrorResponse | undefined;
    const message =
      data?.message || data?.detail || 'An unexpected error occurred';
    toast.error(message);
  } else {
    toast.error('Something went wrong');
  }
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: (failureCount, error) => {
        if (error instanceof AxiosError) {
          const status = error.response?.status;
          if (status === 401 || status === 403 || status === 404) return false;
        }
        return failureCount < 2;
      },
      refetchOnWindowFocus: false,
    },
    mutations: {
      onError: handleQueryError,
    },
  },
});
