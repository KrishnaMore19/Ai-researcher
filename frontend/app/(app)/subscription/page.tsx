// app/(app)/subscription/page.tsx
"use client"
import { Card } from "@/components/card"
import { Button } from "@/components/button"
import { Badge } from "@/components/badge"
import { ProgressBar } from "@/components/progress-bar"
import { Modal } from "@/components/modal"
import { useState, useEffect } from "react"
import { useToast } from "@/components/toast-provider"
import { useSettingsStore } from "@/store"

// Plans matching backend service (subscription_service.py)
const plans = [
  {
    name: "Starter",
    price: 0,
    period: "month",
    features: ["10 documents", "100 AI queries/month", "1GB storage", "Basic support"],
    color: "gray",
    limits: {
      documents_limit: 10,
      queries_limit: 100,
      storage_limit: 1.0
    }
  },
  {
    name: "Pro",
    price: 29.99,
    period: "month",
    features: ["100 documents", "1,000 AI queries/month", "10GB storage", "Priority support", "Advanced analytics"],
    color: "purple",
    isPopular: true,
    limits: {
      documents_limit: 100,
      queries_limit: 1000,
      storage_limit: 10.0
    }
  },
  {
    name: "Enterprise",
    price: 99.99,
    period: "month",
    features: [
      "1,000 documents",
      "10,000 AI queries/month",
      "100GB storage",
      "24/7 support",
      "Custom integrations",
      "API access",
    ],
    color: "blue",
    limits: {
      documents_limit: 1000,
      queries_limit: 10000,
      storage_limit: 100.0
    }
  },
]

export default function SubscriptionPage() {
  const { showToast } = useToast()
  
  // Zustand store
  const {
    subscription,
    billingHistory,
    loading,
    paymentModal,
    fetchSubscription,
    upgradeSubscription,
    verifyPayment,
    fetchBillingHistory,
    openPaymentModal,
    closePaymentModal
  } = useSettingsStore()
  
  const [processing, setProcessing] = useState(false)
  const [razorpayLoaded, setRazorpayLoaded] = useState(false)

  // Fetch subscription and billing on mount + load Razorpay script
  useEffect(() => {
    fetchSubscription()
    fetchBillingHistory()
    
    // Load Razorpay script
    const script = document.createElement("script")
    script.src = "https://checkout.razorpay.com/v1/checkout.js"
    script.async = true
    script.onload = () => setRazorpayLoaded(true)
    script.onerror = () => {
      console.error("Failed to load Razorpay script")
      setRazorpayLoaded(false)
    }
    document.body.appendChild(script)
    
    return () => {
      if (document.body.contains(script)) {
        document.body.removeChild(script)
      }
    }
  }, [fetchSubscription, fetchBillingHistory])

  async function upgrade(planName: string, price: number) {
    try {
      const result = await upgradeSubscription(planName)
      
      if (result.requires_payment && result.order_id) {
        // Open Razorpay checkout for paid plans
        if (!razorpayLoaded) {
          showToast("Payment gateway loading... Please try again.", "info")
          return
        }
        openRazorpayCheckout(result)
      } else {
        // Free plan - upgraded directly
        showToast(`Successfully switched to ${planName} plan`, "success")
        fetchSubscription()
        fetchBillingHistory()
      }
    } catch (err: any) {
      showToast(err.message || "Failed to upgrade", "error")
    }
  }

  function openRazorpayCheckout(paymentData: any) {
    if (typeof window === "undefined" || !(window as any).Razorpay) {
      showToast("Payment gateway not loaded. Please refresh the page.", "error")
      return
    }

    const options = {
      key: paymentData.key_id,
      amount: paymentData.amount_in_paise,
      currency: paymentData.currency || "INR",
      name: "Your App Name",
      description: `${paymentData.plan_name} Plan Subscription`,
      order_id: paymentData.order_id,
      prefill: {
        email: paymentData.user_email,
        contact: paymentData.user_phone,
      },
      theme: {
        color: "#8b5cf6",
      },
      handler: async function (response: any) {
        await handlePaymentSuccess(response)
      },
      modal: {
        ondismiss: function () {
          showToast("Payment cancelled", "info")
          closePaymentModal()
        },
      },
    }

    const razorpay = new (window as any).Razorpay(options)
    razorpay.open()
  }

  async function handlePaymentSuccess(response: any) {
    setProcessing(true)
    try {
      await verifyPayment(
        response.razorpay_order_id,
        response.razorpay_payment_id,
        response.razorpay_signature
      )
      setProcessing(false)
      showToast("Payment successful! Subscription upgraded.", "success")
      closePaymentModal()
      fetchSubscription()
      fetchBillingHistory()
    } catch (err: any) {
      setProcessing(false)
      showToast(err.message || "Payment verification failed", "error")
    }
  }

  // Get current usage from subscription (backend data)
  const currentUsage = subscription ? {
    documents: { used: subscription.documents_used, limit: subscription.documents_limit },
    queries: { used: subscription.queries_used, limit: subscription.queries_limit },
    storage: { used: subscription.storage_used, limit: subscription.storage_limit },
  } : {
    documents: { used: 0, limit: 10 },
    queries: { used: 0, limit: 100 },
    storage: { used: 0, limit: 1 },
  }

  if (loading && !subscription) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-muted-foreground">Loading subscription...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold">Choose Your Plan</h1>
        {subscription && (
          <p className="text-sm text-muted-foreground mt-1">
            Current plan: <strong>{subscription.plan_name}</strong>
          </p>
        )}
      </div>
      
      <div className="grid gap-4 md:grid-cols-3">
        {plans.map((p) => {
          const isCurrent = subscription?.plan_name === p.name
          return (
            <Card key={p.name} glass className="p-5">
              <div className="mb-2 flex items-center justify-between">
                <h3 className="text-lg font-semibold">{p.name}</h3>
                {p.isPopular && <Badge color="purple">POPULAR</Badge>}
                {isCurrent && (
                  <Badge color="blue" variant="subtle">
                    CURRENT PLAN
                  </Badge>
                )}
              </div>
              <div className="mb-3">
                <div className="text-3xl font-bold">
                  {p.price === 0 ? "FREE" : `₹${p.price}`}
                </div>
                <div className="text-sm text-muted-foreground">
                  {p.price === 0 ? "Free Forever" : `per ${p.period}`}
                </div>
              </div>
              <ul className="mb-4 space-y-2 text-sm">
                {p.features.map((f) => (
                  <li key={f} className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                    {f}
                  </li>
                ))}
              </ul>
              <Button
                className="w-full"
                variant={isCurrent ? "ghost" : "primary"}
                disabled={isCurrent || loading}
                onClick={() => upgrade(p.name, p.price)}
              >
                {isCurrent ? "Current Plan" : p.price === 0 ? "Downgrade" : "Upgrade"}
              </Button>
            </Card>
          )
        })}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card glass className="p-5">
          <h3 className="mb-4 text-sm font-semibold text-muted-foreground">Current Usage</h3>
          <div className="space-y-4">
            <div>
              <div className="mb-2 flex items-center justify-between text-sm">
                <span>Documents</span>
                <span>
                  {currentUsage.documents.used}/{currentUsage.documents.limit}
                </span>
              </div>
              <ProgressBar
                value={currentUsage.documents.used}
                max={currentUsage.documents.limit}
                color={
                  currentUsage.documents.used / currentUsage.documents.limit > 0.9
                    ? "red"
                    : currentUsage.documents.used / currentUsage.documents.limit > 0.7
                      ? "yellow"
                      : "green"
                }
              />
            </div>
            <div>
              <div className="mb-2 flex items-center justify-between text-sm">
                <span>AI Queries</span>
                <span>
                  {currentUsage.queries.used}/{currentUsage.queries.limit}
                </span>
              </div>
              <ProgressBar
                value={currentUsage.queries.used}
                max={currentUsage.queries.limit}
                color={
                  currentUsage.queries.used / currentUsage.queries.limit > 0.9
                    ? "red"
                    : currentUsage.queries.used / currentUsage.queries.limit > 0.7
                      ? "yellow"
                      : "green"
                }
              />
            </div>
            <div>
              <div className="mb-2 flex items-center justify-between text-sm">
                <span>Storage</span>
                <span>
                  {currentUsage.storage.used.toFixed(2)}/{currentUsage.storage.limit} GB
                </span>
              </div>
              <ProgressBar
                value={currentUsage.storage.used}
                max={currentUsage.storage.limit}
                color={
                  currentUsage.storage.used / currentUsage.storage.limit > 0.9
                    ? "red"
                    : currentUsage.storage.used / currentUsage.storage.limit > 0.7
                      ? "yellow"
                      : "green"
                }
              />
            </div>
          </div>
        </Card>

        <Card glass className="p-5">
          <h3 className="mb-4 text-sm font-semibold text-muted-foreground">Billing History</h3>
          {billingHistory.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-sm text-muted-foreground">No billing history yet</p>
              <p className="text-xs text-muted-foreground mt-1">Payments will appear here once processed</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-muted-foreground">
                  <tr>
                    <th className="py-2">Date</th>
                    <th className="py-2">Invoice</th>
                    <th className="py-2">Amount</th>
                    <th className="py-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {billingHistory.map((b) => (
                    <tr key={b.id} className="border-t hover:bg-muted/10">
                      <td className="py-2">{new Date(b.date).toLocaleDateString()}</td>
                      <td className="py-2 font-mono text-xs">{b.invoice_number}</td>
                      <td className="py-2">₹{b.amount.toFixed(2)}</td>
                      <td className="py-2">
                        <Badge color={b.status === "Paid" ? "green" : "yellow"}>
                          {b.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>

      <Modal
        isOpen={paymentModal.isOpen}
        onClose={closePaymentModal}
        title={`Upgrade to ${paymentModal.planName}`}
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={closePaymentModal} disabled={processing}>
              Close
            </Button>
          </div>
        }
      >
        <div className="space-y-3 text-sm">
          <div className="rounded-lg border p-3 bg-muted/5">
            <div className="flex justify-between mb-2">
              <span className="text-muted-foreground">Plan:</span>
              <strong>{paymentModal.planName}</strong>
            </div>
            <div className="flex justify-between mb-2">
              <span className="text-muted-foreground">Price:</span>
              <strong>₹{paymentModal.amount}/month</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Next billing:</span>
              <strong>{new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toLocaleDateString()}</strong>
            </div>
          </div>
          <div className="p-3 bg-muted/20 rounded-lg text-center">
            {processing ? (
              <div className="flex items-center justify-center gap-2">
                <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
                <span>Processing payment...</span>
              </div>
            ) : (
              <div>
                <p className="mb-2">Payment gateway will open in a new window.</p>
                <p className="text-xs text-muted-foreground">Complete the payment to upgrade your subscription.</p>
              </div>
            )}
          </div>
        </div>
      </Modal>
    </div>
  )
}