"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Plus, Edit, Trash2, Play, Copy } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useToast } from "@/hooks/use-toast"

interface Template {
  id: string
  name: string
  description: string
  system_prompt: string
  user_prompt: string
  model: string
  is_builtin: boolean
  version: number
  created_at: string
  vars_json: Record<string, string>
}

// Mock templates data
const mockTemplates: Template[] = [
  {
    id: "title-generator",
    name: "Title Tag Generator",
    description: "Generate optimized page titles for better SEO and click-through rates",
    system_prompt: "You are an expert SEO copywriter. Your task is to create compelling, SEO-optimized page titles...",
    user_prompt: "Create an optimized title tag for this page:\n\nURL: {url}\nCurrent Title: {title}\nH1: {h1}...",
    model: "gpt-4-turbo",
    is_builtin: true,
    version: 1,
    created_at: "2024-01-01T00:00:00Z",
    vars_json: {
      url: "Page URL",
      title: "Current title",
      h1: "Main heading",
      content_excerpt: "First 500 chars of content"
    }
  },
  {
    id: "meta-description",
    name: "Meta Description Generator",
    description: "Write compelling meta descriptions that improve click-through rates",
    system_prompt: "You are an expert SEO copywriter specializing in meta descriptions...",
    user_prompt: "Create an optimized meta description for this page:\n\nURL: {url}\nCurrent Description: {description}...",
    model: "gpt-4-turbo",
    is_builtin: true,
    version: 1,
    created_at: "2024-01-01T00:00:00Z",
    vars_json: {
      url: "Page URL",
      description: "Current meta description",
      title: "Page title",
      content_excerpt: "First 1000 chars of content"
    }
  },
  {
    id: "keywords-extract",
    name: "Primary Keywords Extractor",
    description: "Identify and extract primary and secondary keywords from page content",
    system_prompt: "You are an expert SEO keyword analyst...",
    user_prompt: "Analyze this page and extract the most relevant keywords...",
    model: "gpt-4-turbo",
    is_builtin: true,
    version: 1,
    created_at: "2024-01-01T00:00:00Z",
    vars_json: {
      url: "Page URL",
      title: "Page title",
      h1: "Main heading",
      content_excerpt: "First 2000 chars of content"
    }
  },
  {
    id: "content-score",
    name: "SEO Content Scorer",
    description: "Analyze and score page content for SEO effectiveness",
    system_prompt: "You are an expert SEO auditor...",
    user_prompt: "Analyze and score this page for SEO effectiveness...",
    model: "gpt-4-turbo",
    is_builtin: true,
    version: 1,
    created_at: "2024-01-01T00:00:00Z",
    vars_json: {
      url: "Page URL",
      title: "Page title",
      word_count: "Total word count",
      content_excerpt: "First 3000 chars of content"
    }
  },
  {
    id: "schema-generator",
    name: "JSON-LD Schema Generator",
    description: "Generate structured data markup for better search engine understanding",
    system_prompt: "You are an expert in structured data and JSON-LD schema markup...",
    user_prompt: "Generate appropriate JSON-LD schema markup for this page...",
    model: "gpt-4-turbo",
    is_builtin: true,
    version: 1,
    created_at: "2024-01-01T00:00:00Z",
    vars_json: {
      url: "Page URL",
      title: "Page title",
      content_excerpt: "First 2000 chars of content",
      page_type: "Page type (article, product, etc.)"
    }
  }
]

export default function TemplatesPage() {
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const { toast } = useToast()

  // In a real app, this would fetch from the API
  const { data: templates = [], isLoading } = useQuery({
    queryKey: ["templates"],
    queryFn: async () => {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      return mockTemplates
    },
  })

  const handleRunTemplate = (template: Template) => {
    toast({
      title: "Template Ready",
      description: `"${template.name}" is ready to run. Select pages in the Pages view to apply this template.`,
    })
  }

  const handleCopyTemplate = (template: Template) => {
    setSelectedTemplate({
      ...template,
      id: `${template.id}-copy`,
      name: `${template.name} (Copy)`,
      is_builtin: false,
      version: 1
    })
    setIsCreateDialogOpen(true)
  }

  const builtinTemplates = templates.filter(t => t.is_builtin)
  const customTemplates = templates.filter(t => !t.is_builtin)

  const stats = {
    total: templates.length,
    builtin: builtinTemplates.length,
    custom: customTemplates.length,
    models: Array.from(new Set(templates.map(t => t.model))).length
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Prompt Templates</h1>
          <p className="text-muted-foreground">
            Manage AI prompt templates for automated SEO content generation.
          </p>
        </div>
        <Button onClick={() => setIsCreateDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Create Template
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Templates</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-muted-foreground">Available for use</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Built-in</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.builtin}</div>
            <p className="text-xs text-muted-foreground">Ready-to-use templates</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Custom</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.custom}</div>
            <p className="text-xs text-muted-foreground">Your created templates</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">AI Models</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.models}</div>
            <p className="text-xs text-muted-foreground">Different models used</p>
          </CardContent>
        </Card>
      </div>

      {/* Built-in Templates */}
      <Card>
        <CardHeader>
          <CardTitle>Built-in Templates</CardTitle>
          <CardDescription>
            Professional SEO templates ready to use out of the box.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {builtinTemplates.map((template) => (
              <Card key={template.id} className="cursor-pointer hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <CardTitle className="text-lg">{template.name}</CardTitle>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary">Built-in</Badge>
                        <Badge variant="outline">{template.model}</Badge>
                      </div>
                    </div>
                  </div>
                  <CardDescription className="text-sm">
                    {template.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex items-center justify-between">
                    <div className="text-xs text-muted-foreground">
                      {Object.keys(template.vars_json).length} variables
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRunTemplate(template)}
                      >
                        <Play className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCopyTemplate(template)}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Custom Templates */}
      {customTemplates.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Custom Templates</CardTitle>
            <CardDescription>
              Templates you've created or customized for your specific needs.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {customTemplates.map((template) => (
                <Card key={template.id} className="cursor-pointer hover:shadow-md transition-shadow">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <CardTitle className="text-lg">{template.name}</CardTitle>
                        <div className="flex items-center gap-2">
                          <Badge>Custom</Badge>
                          <Badge variant="outline">{template.model}</Badge>
                        </div>
                      </div>
                    </div>
                    <CardDescription className="text-sm">
                      {template.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="flex items-center justify-between">
                      <div className="text-xs text-muted-foreground">
                        v{template.version} • {Object.keys(template.vars_json).length} variables
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRunTemplate(template)}
                        >
                          <Play className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedTemplate(template)
                            setIsEditDialogOpen(true)
                          }}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={isCreateDialogOpen || isEditDialogOpen} onOpenChange={(open) => {
        setIsCreateDialogOpen(open && isCreateDialogOpen)
        setIsEditDialogOpen(open && isEditDialogOpen)
        if (!open) setSelectedTemplate(null)
      }}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {isCreateDialogOpen ? "Create Template" : "Edit Template"}
            </DialogTitle>
            <DialogDescription>
              {isCreateDialogOpen ? "Create a new custom prompt template." : "Modify your custom template."}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Template Name</Label>
                <Input
                  id="name"
                  placeholder="My Custom Template"
                  defaultValue={selectedTemplate?.name || ""}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="model">AI Model</Label>
                <Select defaultValue={selectedTemplate?.model || "gpt-4-turbo"}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select model" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="gpt-4-turbo">GPT-4 Turbo</SelectItem>
                    <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                    <SelectItem value="claude-3-opus">Claude 3 Opus</SelectItem>
                    <SelectItem value="claude-3-sonnet">Claude 3 Sonnet</SelectItem>
                    <SelectItem value="llama-2-70b">Llama 2 70B</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Describe what this template does..."
                defaultValue={selectedTemplate?.description || ""}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="system-prompt">System Prompt</Label>
              <Textarea
                id="system-prompt"
                placeholder="You are an expert SEO specialist..."
                className="min-h-[100px]"
                defaultValue={selectedTemplate?.system_prompt || ""}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="user-prompt">User Prompt Template</Label>
              <Textarea
                id="user-prompt"
                placeholder="Analyze this page: {url}..."
                className="min-h-[150px]"
                defaultValue={selectedTemplate?.user_prompt || ""}
              />
              <p className="text-sm text-muted-foreground">
                Use variables like {"{url}"}, {"{title}"}, {"{content}"} that will be replaced with actual page data.
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setIsCreateDialogOpen(false)
              setIsEditDialogOpen(false)
              setSelectedTemplate(null)
            }}>
              Cancel
            </Button>
            <Button onClick={() => {
              toast({
                title: "Template Saved",
                description: "Your template has been saved successfully.",
              })
              setIsCreateDialogOpen(false)
              setIsEditDialogOpen(false)
              setSelectedTemplate(null)
            }}>
              {isCreateDialogOpen ? "Create Template" : "Save Changes"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
