// app/(app)/notes/page.tsx
"use client"
import { useMemo, useState, useEffect } from "react"
import { Card } from "@/components/card"
import { Button } from "@/components/button"
import { Modal } from "@/components/modal"
import { Badge } from "@/components/badge"
import { useToast } from "@/components/toast-provider"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useNotesStore, useDocumentStore } from "@/store"

function renderMarkdown(md: string) {
  const html = md
    .replace(/^### (.*$)/gim, "<h3>$1</h3>")
    .replace(/^## (.*$)/gim, "<h2>$1</h2>")
    .replace(/^# (.*$)/gim, "<h1>$1</h1>")
    .replace(/\*\*(.*)\*\*/gim, "<strong>$1</strong>")
    .replace(/\n\* (.*)/gim, "<li>$1</li>")
    .replace(/\n- (.*)/gim, "<li>$1</li>")
    .replace(/\n/g, "<br />")
  return html
}

export default function NotesPage() {
  const { showToast } = useToast()
  
  // Zustand stores
  const { 
    notes, 
    loading, 
    fetchNotes, 
    createNote, 
    updateNote, 
    deleteNote,
    togglePin 
  } = useNotesStore()
  
  const { documents, fetchDocuments } = useDocumentStore()
  
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState("")
  const [content, setContent] = useState("")
  const [tags, setTags] = useState<string[]>([])
  const [tagText, setTagText] = useState("")
  const [pinned, setPinned] = useState(false)
  const [link, setLink] = useState<string | null>(null)
  const [tab, setTab] = useState<"write" | "preview">("write")
  const [q, setQ] = useState("")
  const [filterTag, setFilterTag] = useState<string | null>(null)

  // Fetch notes and documents on mount
  useEffect(() => {
    fetchNotes()
    fetchDocuments()
  }, [fetchNotes, fetchDocuments])

  const filtered = useMemo(() => {
    return notes.filter((n) => {
      const matches =
        n.title.toLowerCase().includes(q.toLowerCase()) || 
        n.content.toLowerCase().includes(q.toLowerCase())
      const tagOk = !filterTag || n.tags.includes(filterTag)
      return matches && tagOk
    })
  }, [notes, q, filterTag])

  const pinnedNotes = filtered.filter((n) => n.is_pinned)
  const otherNotes = filtered.filter((n) => !n.is_pinned)

  function addTag() {
    const t = tagText.trim()
    if (!t) return
    setTags((ts) => Array.from(new Set([...ts, t])))
    setTagText("")
  }

  async function saveNote() {
    if (!title || !content) {
      showToast("Please add title and content", "warning")
      return
    }

    try {
      await createNote(title, content, tags, link || undefined)
      setOpen(false)
      setTitle("")
      setContent("")
      setTags([])
      setPinned(false)
      setLink(null)
      showToast("Note saved", "success")
    } catch (err: any) {
      showToast(err.message || "Failed to save note", "error")
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteNote(id)
      showToast("Note deleted", "warning")
    } catch (err: any) {
      showToast(err.message || "Failed to delete note", "error")
    }
  }

  async function handleTogglePin(id: string) {
    try {
      await togglePin(id)
    } catch (err: any) {
      showToast(err.message || "Failed to toggle pin", "error")
    }
  }

  if (loading && notes.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-muted-foreground">Loading notes...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-xl font-semibold">Notes</h1>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-2 rounded-lg border bg-card px-3 py-2">
            <input
              placeholder="Search notes..."
              className="bg-transparent outline-none"
              value={q}
              onChange={(e) => setQ(e.currentTarget.value)}
            />
          </div>
          <div className="flex items-center gap-2 rounded-lg border bg-card px-3 py-2">
            <Select value={filterTag ?? "all"} onValueChange={(v: string) => setFilterTag(v === "all" ? null : v)}>
              <SelectTrigger className="bg-transparent dark:bg-black dark:text-white">
                <SelectValue placeholder="All tags" />
              </SelectTrigger>
              <SelectContent className="dark:bg-black dark:text-white dark:border-white/10">
                <SelectItem value="all">All tags</SelectItem>
                {Array.from(new Set(notes.flatMap((n) => n.tags))).map((t) => (
                  <SelectItem key={t} value={t}>
                    {t}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button onClick={() => setOpen(true)}>Create Note</Button>
        </div>
      </div>

      {pinnedNotes.length > 0 && (
        <>
          <h3 className="text-sm font-semibold text-muted-foreground">Pinned</h3>
          <div className="grid gap-4 sm:grid-cols-2">
            {pinnedNotes.map((n) => (
              <Card key={n.id} glass className="p-4">
                <div className="mb-2 flex items-start justify-between">
                  <h4 className="font-semibold">{n.title}</h4>
                  <Badge color="purple" variant="subtle">
                    Pinned
                  </Badge>
                </div>
                <div
                  className="prose prose-invert max-w-none text-sm"
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(n.content.slice(0, 220)) }}
                />
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  {n.tags.map((t) => (
                    <Badge key={t} color="blue" variant="subtle">
                      #{t}
                    </Badge>
                  ))}
                  {n.document_id && (
                    <Badge color="green" variant="subtle">
                      Linked
                    </Badge>
                  )}
                </div>
                <div className="mt-3 flex items-center justify-end gap-2">
                  <Button variant="ghost" size="sm" onClick={() => handleDelete(n.id)}>
                    Delete
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => handleTogglePin(n.id)}>
                    Unpin
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </>
      )}

      <h3 className="text-sm font-semibold text-muted-foreground">All Notes</h3>
      {otherNotes.length === 0 ? (
        <Card glass className="grid place-items-center gap-2 p-10 text-center">
          <p className="text-muted-foreground">
            {q || filterTag ? "No notes found" : "No notes yet"}
          </p>
          <Button onClick={() => setOpen(true)}>Create Note</Button>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {otherNotes.map((n) => (
            <Card key={n.id} glass className="p-4">
              <div className="mb-2 flex items-start justify-between">
                <h4 className="font-semibold">{n.title}</h4>
                <span className="text-xs text-muted-foreground">
                  {new Date(n.created_at).toLocaleDateString()}
                </span>
              </div>
              <div
                className="prose prose-invert max-w-none text-sm"
                dangerouslySetInnerHTML={{ __html: renderMarkdown(n.content.slice(0, 200)) }}
              />
              <div className="mt-3 flex flex-wrap items-center gap-2">
                {n.tags.map((t) => (
                  <Badge key={t} color="blue" variant="subtle">
                    #{t}
                  </Badge>
                ))}
                {n.document_id && (
                  <Badge color="green" variant="subtle">
                    Linked
                  </Badge>
                )}
              </div>
              <div className="mt-3 flex items-center justify-end gap-2">
                <Button variant="ghost" size="sm" onClick={() => handleDelete(n.id)}>
                  Delete
                </Button>
                <Button variant="ghost" size="sm" onClick={() => handleTogglePin(n.id)}>
                  Pin
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal
        isOpen={open}
        onClose={() => setOpen(false)}
        title="Create New Note"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button onClick={saveNote} loading={loading}>
              Save Note
            </Button>
          </div>
        }
      >
        <div className="space-y-3">
          <label className="block text-sm">
            <span className="mb-1 block text-muted-foreground">Title</span>
            <input
              className="w-full rounded-lg border bg-card px-3 py-2 outline-none focus:ring-2 focus:ring-primary/40"
              value={title}
              onChange={(e) => setTitle(e.currentTarget.value)}
            />
          </label>
          <div>
            <div className="mb-2 flex gap-2 text-xs">
              <button
                className={
                  tab === "write"
                    ? "rounded bg-primary px-2 py-1 text-primary-foreground"
                    : "rounded px-2 py-1 hover:bg-muted/10"
                }
                onClick={() => setTab("write")}
              >
                Write
              </button>
              <button
                className={
                  tab === "preview"
                    ? "rounded bg-primary px-2 py-1 text-primary-foreground"
                    : "rounded px-2 py-1 hover:bg-muted/10"
                }
                onClick={() => setTab("preview")}
              >
                Preview
              </button>
            </div>
            {tab === "write" ? (
              <textarea
                rows={6}
                className="w-full rounded-lg border bg-card p-2 outline-none focus:ring-2 focus:ring-primary/40"
                value={content}
                onChange={(e) => setContent(e.currentTarget.value)}
              />
            ) : (
              <div
                className="prose prose-invert min-h-[144px] rounded-lg border bg-card p-3 text-sm"
                dangerouslySetInnerHTML={{ __html: renderMarkdown(content || "Nothing to preview") }}
              />
            )}
          </div>
          <div className="flex items-center gap-2">
            <input
              className="w-full rounded-lg border bg-card px-3 py-2 outline-none"
              placeholder="Add tag and press Enter"
              value={tagText}
              onChange={(e) => setTagText(e.currentTarget.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault()
                  addTag()
                }
              }}
            />
            <Button variant="ghost" onClick={addTag}>
              Add
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {tags.map((t) => (
              <Badge key={t} color="blue" variant="subtle">
                #{t}
              </Badge>
            ))}
          </div>
          <label className="block text-sm">
            <span className="mb-1 block text-muted-foreground">Link to Document</span>
            <select
              className="w-full rounded-lg border bg-card px-3 py-2 outline-none"
              value={link || ""}
              onChange={(e) => setLink(e.currentTarget.value || null)}
            >
              <option value="">None</option>
              {documents.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.name}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              className="accent-primary"
              checked={pinned}
              onChange={(e) => setPinned(e.currentTarget.checked)}
            />
            Pin this note
          </label>
        </div>
      </Modal>
    </div>
  )
}