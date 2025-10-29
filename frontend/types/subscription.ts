// types/subscription.ts

export interface BillingHistory {
  id: number;
  invoice_number: string;
  amount: number;
  status: string;
  date: string;
}

export interface Subscription {
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

export interface SubscriptionCreate {
  user_id: string;
  plan_name: string;
  price: number;
  period: string;
  active?: boolean;
  documents_used?: number;
  documents_limit?: number;
  queries_used?: number;
  queries_limit?: number;
  storage_used?: number;
  storage_limit?: number;
}

export interface SubscriptionUpdate {
  plan_name?: string;
  active?: boolean;
  documents_used?: number;
  queries_used?: number;
  storage_used?: number;
}

export interface SubscriptionUpgradeRequest {
  plan_name: string;
}

export interface PaymentOrderResponse {
  success: boolean;
  requires_payment: boolean;
  message: string;
  order_id?: string;
  amount?: number;
  amount_in_paise?: number;
  currency?: string;
  plan_name?: string;
  key_id?: string;
  user_email?: string;
  user_phone?: string;
  user_id?: string;
  subscription?: Subscription;
}

export interface PaymentVerificationRequest {
  order_id: string;
  payment_id: string;
  signature: string;
}

export interface PaymentVerificationResponse {
  success: boolean;
  message: string;
  subscription?: Subscription;
  invoice_number?: string;
  order_id?: string;
  payment_id?: string;
}

export interface PaymentModalState {
  isOpen: boolean;
  planName: string | null;
  orderId: string | null;
  amount: number;
  razorpayKeyId: string | null;
}

export interface Plan {
  name: string;
  price: number;
  period: string;
  features: string[];
  documentsLimit: number;
  queriesLimit: number;
  storageLimit: number;
  popular?: boolean;
}

export type PlanName = 'Starter' | 'Pro' | 'Enterprise';

export interface UsageStats {
  documents: {
    used: number;
    limit: number;
    percentage: number;
  };
  queries: {
    used: number;
    limit: number;
    percentage: number;
  };
  storage: {
    used: number;
    limit: number;
    percentage: number;
  };
}

export interface SettingsState {
  subscription: Subscription | null;
  billingHistory: BillingHistory[];
  loading: boolean;
  error: string | null;
  paymentModal: PaymentModalState;
}