import { create } from 'zustand';

interface UiState {
  sidebarOpen: boolean;
  activeRoute: string;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setActiveRoute: (route: string) => void;
}

export const useUiStore = create<UiState>((set) => ({
  sidebarOpen: false,
  activeRoute: '/',

  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setActiveRoute: (route) => set({ activeRoute: route }),
}));
