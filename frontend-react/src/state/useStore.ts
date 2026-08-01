import { create } from "zustand";
import { MedicoBuddyResponse } from "../api/schemas";

export interface MessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  data?: MedicoBuddyResponse;
  requestId?: string;
  parentRequestId?: string | null;
  timestamp: string;
}

export interface UserContextState {
  age_range: string;
  pregnancy_status: string;
  chronic_conditions: string[];
  allergies: string[];
  current_medicines: string[];
  immunocompromised: boolean;
  region: string;
}

interface AppStore {
  threadId: string;
  messages: MessageItem[];
  selectedLanguage: string;
  userContext: UserContextState;
  activeDrawerMessageId: string | null;
  sidebarOpen: boolean;
  highContrast: boolean;
  adminMode: boolean;

  // Actions
  setThreadId: (id: string) => void;
  addMessage: (msg: MessageItem) => void;
  updateMessage: (id: string, updates: Partial<MessageItem>) => void;
  resetConversation: () => void;
  setSelectedLanguage: (lang: string) => void;
  setUserContext: (ctx: Partial<UserContextState>) => void;
  setActiveDrawerMessageId: (id: string | null) => void;
  setSidebarOpen: (open: boolean) => void;
  setHighContrast: (enabled: boolean) => void;
  setAdminMode: (enabled: boolean) => void;
}

export const useStore = create<AppStore>((set) => ({
  threadId: crypto.randomUUID(),
  messages: [],
  selectedLanguage: "auto",
  userContext: {
    age_range: "18_65",
    pregnancy_status: "unknown", // Unknown / Not Pregnant MUST never be interpreted as pregnant
    chronic_conditions: [],
    allergies: [],
    current_medicines: [],
    immunocompromised: false,
    region: "IN",
  },
  activeDrawerMessageId: null,
  sidebarOpen: true,
  highContrast: false,
  adminMode: false,

  setThreadId: (id) => set({ threadId: id }),
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  updateMessage: (id, updates) =>
    set((state) => ({
      messages: state.messages.map((m) => (m.id === id ? { ...m, ...updates } : m)),
    })),
  resetConversation: () =>
    set({
      threadId: crypto.randomUUID(),
      messages: [],
      activeDrawerMessageId: null,
    }),
  setSelectedLanguage: (lang) => set({ selectedLanguage: lang }),
  setUserContext: (ctx) =>
    set((state) => ({ userContext: { ...state.userContext, ...ctx } })),
  setActiveDrawerMessageId: (id) => set({ activeDrawerMessageId: id }),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setHighContrast: (enabled) => set({ highContrast: enabled }),
  setAdminMode: (enabled) => set({ adminMode: enabled }),
}));
