// app/(app)/dashboard/page.tsx
"use client"
import { useEffect } from "react"
import { Card } from "@/components/card"
import { Badge } from "@/components/badge"
import { TrendingUp, FileText, MessageSquare, Zap } from "lucide-react"
import {
  LineChart,
  Line,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from "recharts"
import { useAnalyticsStore } from "@/store"

export default function DashboardPage() {
  const { summary, loading, fetchSummary, analytics, fetchAnalytics } = useAnalyticsStore()

  useEffect(() => {
    fetchSummary()
    fetchAnalytics()
  }, [fetchSummary, fetchAnalytics])

  // Derive chart data from analytics
  const uploadTrends = analytics?.document_uploads?.reduce((acc: any[], upload: any) => {
    const date = new Date(upload.timestamp)
    const monthYear = date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
    
    const existing = acc.find(item => item.month === monthYear)
    if (existing) {
      existing.uploads += 1
    } else {
      acc.push({ month: monthYear, uploads: 1 })
    }
    return acc
  }, []) || []

  const topDocuments = analytics?.top_documents || []
  
  const queryDistribution = analytics?.query_history || []

  // Use real data from store or fallback to mock
  const metrics = [
    { 
      label: "Total Documents", 
      value: summary?.total_documents?.toString() || "0", 
      icon: FileText, 
      color: "blue" 
    },
    { 
      label: "Total Queries", 
      value: summary?.total_queries?.toString() || "0", 
      icon: MessageSquare, 
      color: "purple" 
    },
    { 
      label: "Success Rate", 
      value: `${summary?.query_success_rate || 0}%`, 
      icon: TrendingUp, 
      color: "green" 
    },
    { 
      label: "Productivity", 
      value: summary?.productivity_score?.toString() || "0", 
      icon: Zap, 
      color: "yellow" 
    },
  ]

  // Use real data from analytics store
  const uploadData = uploadTrends && uploadTrends.length > 0 ? uploadTrends : [
    { month: "No Data", uploads: 0 },
  ]

  const topDocs = topDocuments && topDocuments.length > 0 ? topDocuments : []

  const queryStats = [
    { 
      name: "Successful", 
      value: summary?.successful_queries || 0, 
      color: "#10B981" 
    },
    { 
      name: "Failed", 
      value: Math.max((summary?.total_queries || 0) - (summary?.successful_queries || 0), 0), 
      color: "#EF4444" 
    },
  ]

  // Custom tooltip for better styling
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="rounded-lg border bg-card p-3 shadow-lg">
          <p className="text-sm font-medium">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm text-muted-foreground">
              {entry.name}: <span className="font-semibold">{entry.value}</span>
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-muted-foreground">Loading analytics...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((m, i) => {
          const Icon = m.icon
          const colorMap: Record<string, "blue" | "purple" | "green" | "yellow"> = {
            blue: "blue",
            purple: "purple", 
            green: "green",
            yellow: "yellow"
          }
          return (
            <Card key={i} glass className="p-5">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-primary/15 p-2 text-primary">
                    <Icon size={18} />
                  </div>
                  <div>
                    <div className="text-2xl font-semibold">{m.value}</div>
                    <div className="text-sm text-muted-foreground">{m.label}</div>
                  </div>
                </div>
                <Badge color={colorMap[m.color] || "blue"} variant="subtle">
                  <Icon size={12} />
                </Badge>
              </div>
            </Card>
          )
        })}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card glass className="lg:col-span-2 p-6">
          <h3 className="mb-4 text-sm font-semibold text-muted-foreground">Document Uploads Over Time</h3>
          {uploadData && uploadData.length > 0 && uploadData[0].month !== "No Data" ? (
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={uploadData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                  <XAxis 
                    dataKey="month" 
                    tick={{ fill: '#9CA3AF', fontSize: 12 }}
                    axisLine={{ stroke: '#374151' }}
                  />
                  <YAxis 
                    tick={{ fill: '#9CA3AF', fontSize: 12 }}
                    axisLine={{ stroke: '#374151' }}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Line
                    type="monotone"
                    dataKey="uploads"
                    stroke="#3B82F6"
                    strokeWidth={3}
                    dot={{ fill: '#3B82F6', r: 4 }}
                    activeDot={{ r: 6 }}
                    name="Uploads"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex items-center justify-center h-64 text-center">
              <div>
                <FileText className="mx-auto mb-3 text-muted-foreground opacity-50" size={48} />
                <p className="text-sm text-muted-foreground">No upload data available yet</p>
                <p className="text-xs text-muted-foreground mt-1">Upload documents to see trends</p>
              </div>
            </div>
          )}
        </Card>

        <Card glass className="p-6">
          <h3 className="mb-4 text-sm font-semibold text-muted-foreground">Query Success Rate</h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie 
                  data={queryStats} 
                  cx="50%" 
                  cy="50%" 
                  innerRadius={50} 
                  outerRadius={80} 
                  paddingAngle={5} 
                  dataKey="value"
                  label={(entry: any) => `${entry.name} ${(entry.percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {queryStats.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 text-center">
            <div className="text-3xl font-bold">
              {summary?.query_success_rate || 0}%
            </div>
            <div className="text-sm text-muted-foreground mt-1">Overall Success</div>
          </div>
          <div className="mt-4 flex items-center justify-center gap-3">
            <div className="flex items-center gap-1">
              <div className="h-3 w-3 rounded-full bg-green-500"></div>
              <span className="text-xs text-muted-foreground">Successful</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="h-3 w-3 rounded-full bg-red-500"></div>
              <span className="text-xs text-muted-foreground">Failed</span>
            </div>
          </div>
        </Card>
      </div>

      <Card glass className="p-6">
        <h3 className="mb-4 text-sm font-semibold text-muted-foreground">Top Documents by Views</h3>
        {topDocs.length > 0 ? (
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart 
                data={topDocs} 
                layout="vertical" 
                margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} horizontal={false} />
                <XAxis 
                  type="number" 
                  tick={{ fill: '#9CA3AF', fontSize: 12 }}
                  axisLine={{ stroke: '#374151' }}
                />
                <YAxis 
                  dataKey="name" 
                  type="category" 
                  width={120}
                  tick={{ fill: '#9CA3AF', fontSize: 12 }}
                  axisLine={{ stroke: '#374151' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar 
                  dataKey="views" 
                  fill="#8B5CF6" 
                  radius={[0, 8, 8, 0]}
                  name="Views"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="flex items-center justify-center h-80 text-center">
            <div>
              <FileText className="mx-auto mb-3 text-muted-foreground opacity-50" size={48} />
              <p className="text-sm text-muted-foreground">No document data available yet</p>
              <p className="text-xs text-muted-foreground mt-1">Upload and view documents to see statistics</p>
            </div>
          </div>
        )}
      </Card>
    </div>
  )
}