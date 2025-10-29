// store/useSettingsStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import settingsService from '@/services/settingsService';

interface BillingHistory {
  id: number;
  invoice_number: string;
  amount: number;
  status: string;
  date: string;
}

interface Subscription {
  id: number;
  user_id: string;
  plan_name: string;
  price: number;
  period: string;
  active: boolean;
  documents_used: number;
  documents_limit: number;
  queries_used: number;
  queries_limit: number;
  storage_used: number;
  storage_limit: number;
  start_date: string;
  end_date?: string;
  billing_history: BillingHistory[];
}

interface PaymentModalState {
  isOpen: boolean;
  planName: string | null;
  orderId: string | null;
  amount: number;
  razorpayKeyId: string | null;
}

interface UserPreferences {
  defaultModel: string;
  theme: 'Light' | 'Dark' | 'Auto';
  notifications: 'On' | 'Off';
}

interface SettingsState {
  // State
  subscription: Subscription | null;
  billingHistory: BillingHistory[];
  preferences: UserPreferences;
  loading: boolean;
  error: string | null;
  paymentModal: PaymentModalState;

  // Subscription Actions
  fetchSubscription: () => Promise<void>;
  upgradeSubscription: (planName: string) => Promise<any>;
  verifyPayment: (orderId: string, paymentId: string, signature: string) => Promise<void>;
  fetchBillingHistory: () => Promise<void>;
  openPaymentModal: (planName: string, orderData: any) => void;
  closePaymentModal: () => void;

  // Preferences Actions
  updatePreferences: (preferences: Partial<UserPreferences>) => void;
  setDefaultModel: (model: string) => void;
  setTheme: (theme: 'Light' | 'Dark' | 'Auto') => void;
  setNotifications: (notifications: 'On' | 'Off') => void;
  
  clearError: () => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      // Initial State
      subscription: null,
      billingHistory: [],
      preferences: {
        defaultModel: 'llama',
        theme: 'Dark',
        notifications: 'On',
      },
      loading: false,
      error: null,
      paymentModal: {
        isOpen: false,
        planName: null,
        orderId: null,
        amount: 0,
        razorpayKeyId: null,
      },

      // Fetch Subscription
      fetchSubscription: async () => {
        set({ loading: true, error: null });
        try {
          const subscription = await settingsService.getSubscription();
          set({ subscription, loading: false });
        } catch (error: any) {
          set({ loading: false, error: error.message || 'Failed to fetch subscription' });
        }
      },

      // Upgrade Subscription
      upgradeSubscription: async (planName: string) => {
        set({ loading: true, error: null });
        try {
          const result = await settingsService.upgradeSubscription(planName);

          if (result.requires_payment) {
            // Open payment modal with order details
            get().openPaymentModal(planName, result);
            set({ loading: false });
            return result;
          } else {
            // Free plan upgrade - refresh subscription
            await get().fetchSubscription();
            set({ loading: false });
            return result;
          }
        } catch (error: any) {
          set({ loading: false, error: error.message || 'Failed to upgrade subscription' });
          throw error;
        }
      },

      // Verify Payment
      verifyPayment: async (orderId: string, paymentId: string, signature: string) => {
        set({ loading: true, error: null });
        try {
          await settingsService.verifyPayment(orderId, paymentId, signature);
          // Close payment modal
          get().closePaymentModal();
          // Refresh subscription
          await get().fetchSubscription();
          set({ loading: false });
        } catch (error: any) {
          set({ loading: false, error: error.message || 'Payment verification failed' });
          throw error;
        }
      },

      // Fetch Billing History
      fetchBillingHistory: async () => {
        set({ loading: true, error: null });
        try {
          const billingHistory = await settingsService.getBillingHistory();
          set({ billingHistory, loading: false });
        } catch (error: any) {
          set({ loading: false, error: error.message || 'Failed to fetch billing history' });
        }
      },

      // Open Payment Modal
      openPaymentModal: (planName: string, orderData: any) => {
        set({
          paymentModal: {
            isOpen: true,
            planName,
            orderId: orderData.order_id,
            amount: orderData.amount,
            razorpayKeyId: orderData.key_id,
          },
        });
      },

      // Close Payment Modal
      closePaymentModal: () => {
        set({
          paymentModal: {
            isOpen: false,
            planName: null,
            orderId: null,
            amount: 0,
            razorpayKeyId: null,
          },
        });
      },

      // Update Preferences (batch update)
      updatePreferences: (newPreferences: Partial<UserPreferences>) => {
        set((state) => ({
          preferences: {
            ...state.preferences,
            ...newPreferences,
          },
        }));
      },

      // Set Default Model
      setDefaultModel: (model: string) => {
        set((state) => ({
          preferences: {
            ...state.preferences,
            defaultModel: model,
          },
        }));
      },

      // Set Theme
      setTheme: (theme: 'Light' | 'Dark' | 'Auto') => {
        set((state) => ({
          preferences: {
            ...state.preferences,
            theme,
          },
        }));

        // Apply theme to document
        if (typeof document !== 'undefined') {
          if (theme === 'Dark') {
            document.documentElement.classList.add('dark');
          } else if (theme === 'Light') {
            document.documentElement.classList.remove('dark');
          } else {
            // Auto - use system preference
            const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.documentElement.classList.toggle('dark', isDark);
          }
        }
      },

      // Set Notifications
      setNotifications: (notifications: 'On' | 'Off') => {
        set((state) => ({
          preferences: {
            ...state.preferences,
            notifications,
          },
        }));
      },

      // Clear Error
      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'settings-storage',
      partialize: (state) => ({
        preferences: state.preferences,
      }),
    }
  )
);