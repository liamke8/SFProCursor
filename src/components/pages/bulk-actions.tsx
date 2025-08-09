"use client"

import { useState } from "react"
import { Zap, Download, Upload, Trash2, Filter } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { Page } from "./columns"

interface BulkActionsProps {
  selectedPages: Page[]
  onRunPrompt: (templateId: string, pageIds: string[]) => void
  onExport: (pageIds: string[]) => void
  onPublish: (pageIds: string[]) => void
}

export function BulkActions({
  selectedPages,
  onRunPrompt,
  onExport,
  onPublish,
}: BulkActionsProps) {
  const [promptDialogOpen, setPromptDialogOpen] = useState(false)
  const selectedCount = selectedPages.length

  if (selectedCount === 0) return null

  const pageIds = selectedPages.map(page => page.id)

  // Quick prompt templates
  const quickTemplates = [
    { id: "title-generator", name: "Generate Titles", description: "Create optimized page titles" },
    { id: "meta-description", name: "Generate Descriptions", description: "Write compelling meta descriptions" },
    { id: "keywords-extract", name: "Extract Keywords", description: "Identify primary keywords" },
    { id: "content-score", name: "Score Content", description: "Rate SEO quality" },
  ]

  return (
    <div className="flex items-center gap-2">
      <Badge variant="secondary" className="mr-2">
        {selectedCount} selected
      </Badge>

      {/* Quick AI Actions */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button size="sm" className="h-8">
            <Zap className="mr-2 h-4 w-4" />
            Run AI
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel>Quick Templates</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {quickTemplates.map((template) => (
            <DropdownMenuItem
              key={template.id}
              onClick={() => onRunPrompt(template.id, pageIds)}
            >
              <div>
                <div className="font-medium">{template.name}</div>
                <div className="text-xs text-muted-foreground">
                  {template.description}
                </div>
              </div>
            </DropdownMenuItem>
          ))}
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => setPromptDialogOpen(true)}>
            <Zap className="mr-2 h-4 w-4" />
            Custom Template...
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Export Actions */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="h-8">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuLabel>Export Options</DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => onExport(pageIds)}>
            Export to CSV
          </DropdownMenuItem>
          <DropdownMenuItem>
            Export for Review
          </DropdownMenuItem>
          <DropdownMenuItem>
            Export Generated Content
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Publishing Actions */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="h-8">
            <Upload className="mr-2 h-4 w-4" />
            Publish
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuLabel>Publishing Options</DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => onPublish(pageIds)}>
            Publish to WordPress
          </DropdownMenuItem>
          <DropdownMenuItem>
            Send as Draft
          </DropdownMenuItem>
          <DropdownMenuItem>
            Queue for Approval
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Custom Prompt Dialog */}
      <Dialog open={promptDialogOpen} onOpenChange={setPromptDialogOpen}>
        <DialogContent className="sm:max-w-[525px]">
          <DialogHeader>
            <DialogTitle>Run Custom Template</DialogTitle>
            <DialogDescription>
              Select a prompt template to run on {selectedCount} selected pages.
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <h4 className="font-medium">Available Templates</h4>
              <div className="grid gap-2">
                {quickTemplates.map((template) => (
                  <Button
                    key={template.id}
                    variant="outline"
                    className="justify-start h-auto p-3"
                    onClick={() => {
                      onRunPrompt(template.id, pageIds)
                      setPromptDialogOpen(false)
                    }}
                  >
                    <div className="text-left">
                      <div className="font-medium">{template.name}</div>
                      <div className="text-xs text-muted-foreground">
                        {template.description}
                      </div>
                    </div>
                  </Button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="font-medium">Configuration</h4>
              <div className="text-sm text-muted-foreground">
                • Model: GPT-4 Turbo
                • Variants: 1 per page
                • Context: Title, H1, Content excerpt
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setPromptDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => setPromptDialogOpen(false)}>
              Configure Advanced...
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
