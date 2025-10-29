// services/settingsService.ts
import api from './api';
import { config } from '@/lib/config';

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

interface SubscriptionUpgradeRequest {
  plan_name: string;
}

interface PaymentOrderResponse {
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

interface PaymentVerificationRequest {
  order_id: string;
  payment_id: string;
  signature: string;
}

interface PaymentVerificationResponse {
  success: boolean;
  message: string;
  subscription?: Subscription;
  invoice_number?: string;
  order_id?: string;
  payment_id?: string;
}

class SettingsService {
  /**
   * Check if subscriptions feature is enabled
   */
  private checkFeatureEnabled(): void {
    if (!config.features.subscriptions) {
      throw new Error('Subscriptions feature is disabled');
    }
  }

  /**
   * Get current user subscription
   */
  async getSubscription(): Promise<Subscription> {
    this.checkFeatureEnabled();

    const response = await api.get<Subscription>('/settings/subscription');
    return response.data;
  }

  /**
   * Upgrade subscription plan
   */
  async upgradeSubscription(planName: string): Promise<PaymentOrderResponse> {
    this.checkFeatureEnabled();

    const request: SubscriptionUpgradeRequest = {
      plan_name: planName,
    };

    const response = await api.post<PaymentOrderResponse>(
      '/settings/subscription/upgrade',
      request
    );
    return response.data;
  }

  /**
   * Verify payment after Razorpay checkout
   */
  async verifyPayment(
    orderId: string,
    paymentId: string,
    signature: string
  ): Promise<PaymentVerificationResponse> {
    this.checkFeatureEnabled();

    const request: PaymentVerificationRequest = {
      order_id: orderId,
      payment_id: paymentId,
      signature: signature,
    };

    const response = await api.post<PaymentVerificationResponse>(
      '/settings/subscription/verify-payment',
      request
    );
    return response.data;
  }

  /**
   * Get billing history
   */
  async getBillingHistory(): Promise<BillingHistory[]> {
    this.checkFeatureEnabled();

    const response = await api.get<BillingHistory[]>('/settings/billing-history');
    return response.data;
  }

  /**
   * Add billing record (for testing)
   */
  async addBillingRecord(
    amount: number,
    invoiceNumber: string,
    status: string = 'Paid'
  ): Promise<BillingHistory> {
    this.checkFeatureEnabled();

    const response = await api.post<BillingHistory>('/settings/billing/add-record', null, {
      params: {
        amount,
        invoice_number: invoiceNumber,
        status,
      },
    });
    return response.data;
  }

  /**
   * Calculate usage percentage
   */
  calculateUsagePercentage(used: number, limit: number): number {
    if (limit === 0) return 0;
    return Math.round((used / limit) * 100);
  }

  /**
   * Check if usage limit reached
   */
  isLimitReached(used: number, limit: number): boolean {
    return used >= limit;
  }

  /**
   * Format storage size
   */
  formatStorage(sizeInMB: number): string {
    if (sizeInMB < 1024) {
      return `${sizeInMB.toFixed(2)} MB`;
    }
    return `${(sizeInMB / 1024).toFixed(2)} GB`;
  }

  /**
   * Get plan features
   */
  getPlanFeatures(planName: string): string[] {
    const features: Record<string, string[]> = {
      Starter: [
        '10 Document Uploads',
        '50 AI Queries/month',
        '500 MB Storage',
        'Basic Support',
        'Single Model Access',
      ],
      Pro: [
        '100 Document Uploads',
        '500 AI Queries/month',
        '5 GB Storage',
        'Priority Support',
        'Multi-Model Access',
        'Advanced Search',
        'Citation Extraction',
      ],
      Enterprise: [
        'Unlimited Documents',
        'Unlimited AI Queries',
        '50 GB Storage',
        '24/7 Premium Support',
        'All Models Access',
        'Advanced Features',
        'API Access',
        'Custom Integrations',
      ],
    };

    return features[planName] || [];
  }

  /**
   * Get plan price
   */
  getPlanPrice(planName: string): number {
    const prices: Record<string, number> = {
      Starter: 0,
      Pro: 999,
      Enterprise: 2999,
    };

    return prices[planName] || 0;
  }

  /**
   * Format currency
   */
  formatCurrency(amount: number): string {
    return `₹${amount.toFixed(2)}`;
  }

  /**
   * Get Razorpay key from config
   */
  getRazorpayKey(): string {
    return config.razorpayKeyId;
  }

  /**
   * Check if plan upgrade is available
   */
  canUpgradeTo(currentPlan: string, targetPlan: string): boolean {
    const planHierarchy = ['Starter', 'Pro', 'Enterprise'];
    const currentIndex = planHierarchy.indexOf(currentPlan);
    const targetIndex = planHierarchy.indexOf(targetPlan);
    
    return targetIndex > currentIndex;
  }

  /**
   * Get usage warning level
   */
  getUsageWarningLevel(used: number, limit: number): 'safe' | 'warning' | 'danger' {
    const percentage = this.calculateUsagePercentage(used, limit);
    
    if (percentage >= 90) return 'danger';
    if (percentage >= 75) return 'warning';
    return 'safe';
  }
}

export default new SettingsService();