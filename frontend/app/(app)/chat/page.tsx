// app/(app)/chat/page.tsx
"use client"
import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/button"
import { Card } from "@/components/card"
import { cn } from "@/lib/utils"
import { Copy, Send, Trash2, FileText } from "lucide-react"
import { useToast } from "@/components/toast-provider"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useChatStore, useDocumentStore, useSettingsStore } from "@/store"

const models = [
  { id: "llama", name: "Llama 3.1", icon: "🦙" },
  { id: "dolphin", name: "Dolphin 2.9", icon: "🐬" },
  { id: "gemma", name: "Gemma 2", icon: "💎" },
]

function renderMarkdown(text: string) {
  const withBold = text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
  const withLines = withBold.replace(/\n/g, "<br/>")
  return withLines
}

export default function ChatPage() {
  const { showToast } = useToast()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  // Zustand stores
  const { 
    messages, 
    loading, 
    selectedModel, 
    selectedDocuments,
    currentMessage,
    sendMessage, 
    deleteMessage,
    fetchHistory,
    setModel,
    setDocuments,
    setCurrentMessage 
  } = useChatStore()
  
  const { documents, fetchDocuments } = useDocumentStore()
  
  // Get default model from settings
  const { preferences } = useSettingsStore()
  
  const [text, setText] = useState("")

  // Fetch chat history and documents on mount
  useEffect(() => {
    fetchHistory()
    fetchDocuments()
  }, [fetchHistory, fetchDocuments])

  // Set default model from preferences on mount
  useEffect(() => {
    if (preferences.defaultModel) {
      setModel(preferences.defaultModel)
    }
  }, [preferences.defaultModel, setModel])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  function toggleDoc(id: string) {
    setDocuments(
      selectedDocuments.includes(id)
        ? selectedDocuments.filter((x) => x !== id)
        : [...selectedDocuments, id]
    )
  }

  async function send() {
    if (!text.trim()) return
    
    const messageText = text
    setText("")
    
    try {
      await sendMessage(messageText, selectedDocuments)
    } catch (err: any) {
      showToast(err.message || "Failed to send message", "error")
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteMessage(id)
      showToast("Message deleted", "success")
    } catch (err: any) {
      showToast(err.message || "Failed to delete message", "error")
    }
  }

  return (
    <div className="grid gap-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-xl font-semibold">Chat with AI</h1>
        <div className="flex flex-wrap items-center gap-2">
          <div className="rounded-lg border bg-card px-3 py-2">
            <div className="flex items-center gap-2">
              <FileText size={16} className="text-muted-foreground" />
              <div className="flex flex-wrap gap-2">
                {documents.slice(0, 5).map((d) => {
                  const active = selectedDocuments.includes(d.id)
                  return (
                    <button
                      key={d.id}
                      onClick={() => toggleDoc(d.id)}
                      className={cn(
                        "rounded-full border px-2 py-1 text-xs",
                        active ? "bg-primary text-primary-foreground" : "hover:bg-muted/10",
                      )}
                    >
                      {d.name}
                    </button>
                  )
                })}
              </div>
            </div>
          </div>
          <div className="rounded-lg border bg-card px-3 py-2">
            <Select value={selectedModel} onValueChange={setModel}>
              <SelectTrigger className="bg-transparent dark:bg-black dark:text-white">
                <SelectValue placeholder="Select model" />
              </SelectTrigger>
              <SelectContent className="dark:bg-black dark:text-white dark:border-white/10">
                {models.map((m) => (
                  <SelectItem key={m.id} value={m.id}>
                    {m.icon} {m.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <Card glass className="h-[60vh] overflow-y-auto p-4">
        <div className="space-y-4">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              <p>Start a conversation by typing a message below</p>
            </div>
          ) : (
            messages.map((m) => (
              <div key={m.id} className={cn("flex", m.sender === "user" ? "justify-end" : "justify-start")}>
                <div
                  className={cn(
                    "max-w-[80%] rounded-2xl p-3 text-sm",
                    m.sender === "user" ? "bg-primary text-primary-foreground" : "bg-card border",
                  )}
                >
                  <div dangerouslySetInnerHTML={{ __html: renderMarkdown(m.content) }} />
                  <div className="mt-2 flex items-center justify-between gap-2 text-[10px] text-muted-foreground">
                    <span>{new Date(m.created_at).toLocaleTimeString()}</span>
                    <span className="flex items-center gap-2 opacity-70">
                      <button
                        className="hover:opacity-100"
                        onClick={() => {
                          navigator.clipboard.writeText(m.content)
                          showToast("Copied message", "success")
                        }}
                        aria-label="Copy"
                      >
                        <Copy size={12} />
                      </button>
                      <button
                        className="hover:opacity-100"
                        onClick={() => handleDelete(m.id)}
                        aria-label="Delete"
                      >
                        <Trash2 size={12} />
                      </button>
                    </span>
                  </div>
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="flex justify-start">
              <div className="rounded-2xl border bg-card p-3 text-sm">
                <span className="mr-2 font-semibold">AI</span>
                <span className="inline-flex items-center gap-1">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:-0.2s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:-0.1s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-primary" />
                </span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </Card>

      <div className="flex items-center gap-2 rounded-xl border bg-card p-2">
        <textarea
          rows={1}
          placeholder="Type message..."
          className="min-h-[44px] w-full resize-none bg-transparent p-2 outline-none"
          value={text}
          onChange={(e) => setText(e.currentTarget.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              send()
            }
          }}
        />
        <Button onClick={send} disabled={loading || !text.trim()}>
          <Send size={16} />
          Send
        </Button>
      </div>
    </div>
  )
}