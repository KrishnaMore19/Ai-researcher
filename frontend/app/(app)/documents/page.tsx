// app/(app)/documents/page.tsx
"use client"
import { useMemo, useState, useEffect, useRef } from "react"
import { Card } from "@/components/card"
import { Button } from "@/components/button"
import { Modal } from "@/components/modal"
import { Badge } from "@/components/badge"
import { ProgressBar } from "@/components/progress-bar"
import { CloudUpload, Download, Eye, FileText, Filter, Search, Trash2, AlertTriangle } from "lucide-react"
import { useToast } from "@/components/toast-provider"
import { useDocumentStore } from "@/store"
import { useRouter } from "next/navigation"

type FilterType = "All" | "PDF" | "TXT" | "DOCX"
type SortType = "Newest" | "Oldest" | "Name" | "Size"

export default function DocumentsPage() {
  const { showToast } = useToast()
  const router = useRouter()
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  // Zustand store
  const { 
    documents, 
    loading, 
    uploading, 
    error, 
    fetchDocuments, 
    uploadDocument, 
    deleteDocument,
    getDocument 
  } = useDocumentStore()
  
  const [query, setQuery] = useState("")
  const [type, setType] = useState<FilterType>("All")
  const [sort, setSort] = useState<SortType>("Newest")
  const [open, setOpen] = useState(false)
  const [progress, setProgress] = useState(0)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [title, setTitle] = useState("")
  const [deleting, setDeleting] = useState<string | null>(null)
  
  // Delete confirmation modal state
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
  const [documentToDelete, setDocumentToDelete] = useState<{ id: string; name: string } | null>(null)
  
  // View document modal state
  const [viewModalOpen, setViewModalOpen] = useState(false)
  const [viewingDocument, setViewingDocument] = useState<any>(null)
  const [loadingView, setLoadingView] = useState(false)

  // Fetch documents on mount
  useEffect(() => {
    fetchDocuments()
  }, [fetchDocuments])

  // Show error toast
  useEffect(() => {
    if (error) {
      showToast(error, "error")
    }
  }, [error, showToast])

  const filtered = useMemo(() => {
    let list = documents.filter((d) => d.name.toLowerCase().includes(query.toLowerCase()))
    if (type !== "All") list = list.filter((d) => d.type === type)
    if (sort === "Newest") list = [...list].sort((a, b) => (a.uploaded_date < b.uploaded_date ? 1 : -1))
    if (sort === "Oldest") list = [...list].sort((a, b) => (a.uploaded_date > b.uploaded_date ? 1 : -1))
    if (sort === "Name") list = [...list].sort((a, b) => a.name.localeCompare(b.name))
    if (sort === "Size") list = [...list].sort((a, b) => parseFloat(b.size) - parseFloat(a.size))
    return list
  }, [documents, query, type, sort])

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) {
      // Check file size (10MB max)
      if (file.size > 10 * 1024 * 1024) {
        showToast("File size must be less than 10MB", "error")
        return
      }
      
      setSelectedFile(file)
      setTitle(file.name.replace(/\.[^/.]+$/, "")) // Remove extension
    }
  }

  function triggerFileInput() {
    fileInputRef.current?.click()
  }

  async function startUpload() {
    if (!selectedFile || !title) {
      showToast("Please select a file and enter a title", "error")
      return
    }

    setProgress(0)
    const interval = setInterval(() => {
      setProgress((p) => Math.min(p + 10, 90))
    }, 150)

    try {
      await uploadDocument(selectedFile, title)
      clearInterval(interval)
      setProgress(100)
      showToast("Upload completed", "success")
      setOpen(false)
      setSelectedFile(null)
      setTitle("")
      setProgress(0)
      fetchDocuments() // Refresh list
    } catch (err: any) {
      clearInterval(interval)
      setProgress(0)
      showToast(err.message || "Upload failed", "error")
    }
  }

  function openDeleteConfirm(id: string, name: string) {
    setDocumentToDelete({ id, name })
    setDeleteConfirmOpen(true)
  }

  function closeDeleteConfirm() {
    setDeleteConfirmOpen(false)
    setDocumentToDelete(null)
  }

  async function confirmDelete() {
    if (!documentToDelete) return
    
    setDeleting(documentToDelete.id)
    setDeleteConfirmOpen(false)
    
    try {
      await deleteDocument(documentToDelete.id)
      showToast("Document deleted successfully", "success")
      // Refresh list after successful deletion
      await fetchDocuments()
    } catch (err: any) {
      console.error("Delete error:", err)
      showToast(err.message || "Failed to delete document", "error")
    } finally {
      setDeleting(null)
      setDocumentToDelete(null)
    }
  }

  async function viewDocument(id: string, name: string) {
    setLoadingView(true)
    setViewModalOpen(true)
    
    try {
      // Fetch document details from store
      await getDocument(id)
      
      // Find the document in the documents array
      const doc = documents.find(d => d.id === id)
      setViewingDocument(doc)
      
      if (doc) {
        showToast(`Viewing ${name}`, "success")
      } else {
        showToast("Document not found", "error")
        setViewModalOpen(false)
      }
    } catch (err: any) {
      showToast(err.message || "Failed to view document", "error")
      setViewModalOpen(false)
    } finally {
      setLoadingView(false)
    }
  }
  
  function closeViewModal() {
    setViewModalOpen(false)
    setViewingDocument(null)
  }

  function downloadDocument(doc: any) {
    try {
      // Create a simple download link
      // Since backend might not have download endpoint, create a placeholder
      const dataStr = `Document: ${doc.name}\nType: ${doc.type}\nSize: ${doc.size}\nUploaded: ${doc.uploaded_date}\nStatus: ${doc.status}`
      const dataBlob = new Blob([dataStr], { type: 'text/plain' })
      const url = window.URL.createObjectURL(dataBlob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${doc.name.replace(/\.[^/.]+$/, "")}_info.txt`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      showToast("Document info downloaded", "success")
    } catch (err: any) {
      console.error("Download error:", err)
      showToast("Failed to download document", "error")
    }
  }

  function handleModalClose() {
    setOpen(false)
    setSelectedFile(null)
    setTitle("")
    setProgress(0)
  }

  if (loading && documents.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-muted-foreground">Loading documents...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h1 className="text-xl font-semibold">Documents</h1>
          <Button onClick={() => setOpen(true)} className="w-full sm:w-auto">
            <CloudUpload size={16} />
            Upload Document
          </Button>
        </div>

        {/* Filters Section - Responsive */}
        <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
          {/* Search */}
          <div className="flex items-center gap-2 rounded-lg border bg-card px-3 py-2 flex-1 sm:flex-initial sm:min-w-[200px]">
            <Search size={16} className="text-muted-foreground flex-shrink-0" />
            <input
              placeholder="Search documents..."
              className="bg-transparent outline-none w-full min-w-0"
              value={query}
              onChange={(e) => setQuery(e.currentTarget.value)}
            />
          </div>

          {/* Filter Type */}
          <div className="flex items-center gap-2 rounded-lg border bg-card px-3 py-2 flex-1 sm:flex-initial">
            <Filter size={16} className="text-muted-foreground flex-shrink-0" />
            <select
              className="bg-transparent outline-none w-full min-w-0"
              value={type}
              onChange={(e) => setType(e.currentTarget.value as FilterType)}
            >
              <option>All</option>
              <option>PDF</option>
              <option>TXT</option>
              <option>DOCX</option>
            </select>
          </div>

          {/* Sort */}
          <div className="flex items-center gap-2 rounded-lg border bg-card px-3 py-2 flex-1 sm:flex-initial">
            <span className="text-sm text-muted-foreground whitespace-nowrap">Sort</span>
            <select
              className="bg-transparent outline-none w-full min-w-0"
              value={sort}
              onChange={(e) => setSort(e.currentTarget.value as SortType)}
            >
              <option>Newest</option>
              <option>Oldest</option>
              <option>Name</option>
              <option>Size</option>
            </select>
          </div>
        </div>
      </div>

      {/* Documents Grid */}
      {filtered.length === 0 ? (
        <Card glass className="grid place-items-center gap-2 p-10 text-center">
          <FileText className="text-muted-foreground" />
          <p className="text-muted-foreground">
            {query ? "No documents found" : "No documents yet"}
          </p>
          <Button onClick={() => setOpen(true)}>Upload Document</Button>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((d) => (
            <Card key={d.id} glass className="p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <div className="rounded-lg bg-primary/15 p-2 text-primary flex-shrink-0">
                    <FileText size={18} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate font-medium">{d.name}</div>
                    <div className="text-xs text-muted-foreground truncate">
                      {d.size} • {d.uploaded_date}
                    </div>
                  </div>
                </div>
                <div className="flex-shrink-0">
                  {d.status === "completed" && <Badge color="green">Completed</Badge>}
                  {d.status === "processing" && <Badge color="yellow">Processing</Badge>}
                  {d.status === "failed" && <Badge color="red">Failed</Badge>}
                </div>
              </div>
              <div className="mt-4 flex flex-wrap items-center justify-end gap-2">
                <Button 
                  variant="ghost" 
                  size="sm" 
                  aria-label="View"
                  onClick={() => viewDocument(d.id, d.name)}
                  className="text-xs"
                >
                  <Eye size={14} />
                  View
                </Button>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  aria-label="Download"
                  onClick={() => downloadDocument(d)}
                  className="text-xs"
                >
                  <Download size={14} />
                  Download
                </Button>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  aria-label="Delete" 
                  onClick={() => openDeleteConfirm(d.id, d.name)}
                  disabled={deleting === d.id}
                  className="text-xs"
                >
                  {deleting === d.id ? (
                    <div className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" />
                  ) : (
                    <>
                      <Trash2 size={14} />
                      Delete
                    </>
                  )}
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      <Modal
        isOpen={open}
        onClose={handleModalClose}
        title="Upload Document"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={handleModalClose} disabled={uploading}>
              Cancel
            </Button>
            <Button onClick={startUpload} loading={uploading} disabled={!selectedFile || !title}>
              Upload
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Document Title</label>
            <input
              type="text"
              className="w-full rounded-lg border bg-card px-3 py-2 outline-none focus:ring-2 focus:ring-primary"
              placeholder="Enter document title"
              value={title}
              onChange={(e) => setTitle(e.currentTarget.value)}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">Select File</label>
            <div 
              className="grid place-items-center gap-3 rounded-xl border-2 border-dashed p-8 text-center cursor-pointer hover:border-primary transition-colors"
              onClick={triggerFileInput}
            >
              <CloudUpload size={32} className="text-primary" />
              <p className="text-sm font-medium break-all px-2">
                {selectedFile ? selectedFile.name : "Click to select file"}
              </p>
              <p className="text-xs text-muted-foreground">
                Supported: PDF, TXT, DOC, DOCX, MD • Max 10MB
              </p>
              {selectedFile && (
                <p className="text-xs text-muted-foreground">
                  Size: {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              )}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,.doc,.docx,.md"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>

          {uploading && progress > 0 && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Uploading...</span>
                <span>{progress}%</span>
              </div>
              <ProgressBar value={progress} max={100} color="blue" />
            </div>
          )}
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={deleteConfirmOpen}
        onClose={closeDeleteConfirm}
        title="Delete Document"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={closeDeleteConfirm}>
              Cancel
            </Button>
            <Button 
              onClick={confirmDelete}
              className="bg-red-500 hover:bg-red-600 text-white"
            >
              Delete
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <div className="flex items-start gap-3">
            <div className="rounded-full bg-red-100 dark:bg-red-900/20 p-2 flex-shrink-0">
              <AlertTriangle className="text-red-600 dark:text-red-500" size={24} />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-medium mb-2">Are you sure?</h3>
              <p className="text-sm text-muted-foreground">
                You are about to delete "<span className="font-medium text-foreground break-all">{documentToDelete?.name}</span>". 
                This action cannot be undone.
              </p>
            </div>
          </div>
        </div>
      </Modal>

      {/* View Document Modal */}
      <Modal
        isOpen={viewModalOpen}
        onClose={closeViewModal}
        title={viewingDocument ? viewingDocument.name : "Document Details"}
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={closeViewModal}>
              Close
            </Button>
            {viewingDocument && (
              <Button onClick={() => downloadDocument(viewingDocument)}>
                <Download size={16} />
                Download
              </Button>
            )}
          </div>
        }
      >
        {loadingView ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
              <p className="text-muted-foreground">Loading document...</p>
            </div>
          </div>
        ) : viewingDocument ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-muted-foreground">Type</label>
                <p className="text-sm font-medium mt-1">{viewingDocument.type}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Size</label>
                <p className="text-sm font-medium mt-1">{viewingDocument.size}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Uploaded</label>
                <p className="text-sm font-medium mt-1 break-all">{viewingDocument.uploaded_date}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Status</label>
                <div className="mt-1">
                  {viewingDocument.status === "completed" && <Badge color="green">Completed</Badge>}
                  {viewingDocument.status === "processing" && <Badge color="yellow">Processing</Badge>}
                  {viewingDocument.status === "failed" && <Badge color="red">Failed</Badge>}
                </div>
              </div>
            </div>

            {/* Document Content Preview */}
            {viewingDocument.content && (
              <div>
                <label className="text-sm font-medium text-muted-foreground mb-2 block">Content Preview</label>
                <div className="rounded-lg border bg-muted/50 p-4 max-h-96 overflow-y-auto overflow-x-auto">
                  <pre className="text-sm whitespace-pre-wrap font-mono break-words">
                    {viewingDocument.content}
                  </pre>
                </div>
              </div>
            )}

            {/* Document URL if available */}
            {viewingDocument.url && (
              <div>
                <label className="text-sm font-medium text-muted-foreground mb-2 block">Document URL</label>
                <a 
                  href={viewingDocument.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline break-all"
                >
                  {viewingDocument.url}
                </a>
              </div>
            )}

            {/* Metadata if available */}
            {viewingDocument.metadata && (
              <div>
                <label className="text-sm font-medium text-muted-foreground mb-2 block">Metadata</label>
                <div className="rounded-lg border bg-muted/50 p-4 overflow-x-auto">
                  <pre className="text-xs whitespace-pre-wrap break-words">
                    {JSON.stringify(viewingDocument.metadata, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* If no additional content */}
            {!viewingDocument.content && !viewingDocument.url && !viewingDocument.metadata && (
              <div className="text-center py-8 text-muted-foreground">
                <FileText size={48} className="mx-auto mb-3 opacity-50" />
                <p className="text-sm">No additional preview available</p>
                <p className="text-xs mt-1">Download the document to view its full content</p>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            <p>Document not found</p>
          </div>
        )}
      </Modal>
    </div>
  )
}