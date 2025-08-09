"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Download, Upload, FileText, Settings, CheckCircle, AlertCircle, Clock } from "lucide-react"

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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { useToast } from "@/hooks/use-toast"

interface Site {
  id: string
  name: string
  domain: string
}

interface ExportJob {
  id: string
  type: "csv_export" | "wordpress_publish"
  site_name: string
  status: "pending" | "completed" | "failed"
  created_at: string
  completed_at?: string
  row_count?: number
  error_message?: string
}

interface WordPressIntegration {
  id: string
  site_id: string
  site_name: string
  wp_url: string
  plugin_type: "yoast" | "rankmath" | "seopress"
  status: "connected" | "error"
}

// Mock data
const mockSites: Site[] = [
  { id: "site-1", name: "Example Company", domain: "example.com" },
  { id: "site-2", name: "Blog Site", domain: "blog.example.com" },
]

const mockExportJobs: ExportJob[] = [
  {
    id: "1",
    type: "csv_export",
    site_name: "example.com",
    status: "completed",
    created_at: "2024-01-15T10:30:00Z",
    completed_at: "2024-01-15T10:31:00Z",
    row_count: 245
  },
  {
    id: "2", 
    type: "wordpress_publish",
    site_name: "blog.example.com",
    status: "pending",
    created_at: "2024-01-15T10:25:00Z"
  },
  {
    id: "3",
    type: "csv_export",
    site_name: "All Sites",
    status: "failed",
    created_at: "2024-01-15T09:45:00Z",
    error_message: "Database connection timeout"
  }
]

const mockWordPressIntegrations: WordPressIntegration[] = [
  {
    id: "wp-1",
    site_id: "site-1",
    site_name: "example.com",
    wp_url: "https://example.com",
    plugin_type: "yoast",
    status: "connected"
  },
  {
    id: "wp-2",
    site_id: "site-2", 
    site_name: "blog.example.com",
    wp_url: "https://blog.example.com",
    plugin_type: "rankmath",
    status: "error"
  }
]

export default function ExportsPage() {
  const [selectedSite, setSelectedSite] = useState<string>("")
  const [exportColumns, setExportColumns] = useState<string[]>([
    "url", "title", "description", "h1", "word_count", "status_code"
  ])
  const [includeGenerated, setIncludeGenerated] = useState(true)
  const [publishContentType, setPublishContentType] = useState<string>("both")
  const [selectedIntegration, setSelectedIntegration] = useState<string>("")
  const [isDryRun, setIsDryRun] = useState(true)
  const { toast } = useToast()

  // In a real app, these would fetch from APIs
  const { data: sites = [] } = useQuery({
    queryKey: ["sites"],
    queryFn: async () => {
      await new Promise(resolve => setTimeout(resolve, 500))
      return mockSites
    },
  })

  const { data: exportJobs = [] } = useQuery({
    queryKey: ["export-jobs"],
    queryFn: async () => {
      await new Promise(resolve => setTimeout(resolve, 500))
      return mockExportJobs
    },
  })

  const { data: wpIntegrations = [] } = useQuery({
    queryKey: ["wp-integrations"],
    queryFn: async () => {
      await new Promise(resolve => setTimeout(resolve, 500))
      return mockWordPressIntegrations
    },
  })

  const availableColumns = [
    { id: "url", label: "URL" },
    { id: "title", label: "Title" },
    { id: "description", label: "Meta Description" },
    { id: "h1", label: "H1 Heading" },
    { id: "word_count", label: "Word Count" },
    { id: "status_code", label: "Status Code" },
    { id: "canonical", label: "Canonical URL" },
    { id: "meta_robots", label: "Meta Robots" },
    { id: "last_crawled", label: "Last Crawled" },
    { id: "missing_title", label: "Missing Title" },
    { id: "missing_description", label: "Missing Description" },
    { id: "thin_content", label: "Thin Content" },
  ]

  const handleExportCSV = async () => {
    toast({
      title: "Export Started",
      description: `Exporting ${selectedSite ? sites.find(s => s.id === selectedSite)?.domain : 'all sites'} data to CSV.`,
    })

    // In a real app, this would call the API
    console.log("Exporting CSV:", {
      site_id: selectedSite,
      columns: exportColumns,
      include_generated: includeGenerated
    })
  }

  const handlePublishToWordPress = async () => {
    if (!selectedIntegration) {
      toast({
        title: "Error",
        description: "Please select a WordPress integration.",
        variant: "destructive"
      })
      return
    }

    toast({
      title: isDryRun ? "Dry Run Started" : "Publishing Started",
      description: `${isDryRun ? 'Testing' : 'Publishing'} ${publishContentType} content to WordPress.`,
    })

    // In a real app, this would call the API
    console.log("Publishing to WordPress:", {
      integration_id: selectedIntegration,
      content_type: publishContentType,
      dry_run: isDryRun
    })
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case "failed":
        return <AlertCircle className="h-4 w-4 text-red-600" />
      case "pending":
        return <Clock className="h-4 w-4 text-yellow-600" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "default"
      case "failed":
        return "destructive"
      case "pending":
        return "secondary"
      default:
        return "outline"
    }
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Export & Publishing</h1>
          <p className="text-muted-foreground">
            Export your SEO data to CSV or publish optimized content directly to WordPress.
          </p>
        </div>
      </div>

      {/* Export Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CSV Export */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download className="h-5 w-5" />
              CSV Export
            </CardTitle>
            <CardDescription>
              Export your page data and generated content to a CSV file for analysis or backup.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Site</Label>
              <Select value={selectedSite} onValueChange={setSelectedSite}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a site or all sites..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All sites</SelectItem>
                  {sites.map((site) => (
                    <SelectItem key={site.id} value={site.id}>
                      {site.name} ({site.domain})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Columns to Export</Label>
              <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto">
                {availableColumns.map((column) => (
                  <div key={column.id} className="flex items-center space-x-2">
                    <Checkbox
                      id={column.id}
                      checked={exportColumns.includes(column.id)}
                      onCheckedChange={(checked) => {
                        if (checked) {
                          setExportColumns([...exportColumns, column.id])
                        } else {
                          setExportColumns(exportColumns.filter(col => col !== column.id))
                        }
                      }}
                    />
                    <Label htmlFor={column.id} className="text-sm">{column.label}</Label>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="include-generated"
                checked={includeGenerated}
                onCheckedChange={setIncludeGenerated}
              />
              <Label htmlFor="include-generated">Include AI-generated content</Label>
            </div>

            <Button onClick={handleExportCSV} className="w-full">
              <FileText className="mr-2 h-4 w-4" />
              Export to CSV
            </Button>
          </CardContent>
        </Card>

        {/* WordPress Publishing */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5" />
              WordPress Publishing
            </CardTitle>
            <CardDescription>
              Publish your AI-generated titles and descriptions directly to WordPress sites.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>WordPress Integration</Label>
              <Select value={selectedIntegration} onValueChange={setSelectedIntegration}>
                <SelectTrigger>
                  <SelectValue placeholder="Select WordPress site..." />
                </SelectTrigger>
                <SelectContent>
                  {wpIntegrations.map((integration) => (
                    <SelectItem key={integration.id} value={integration.id}>
                      <div className="flex items-center justify-between w-full">
                        <span>{integration.site_name}</span>
                        <Badge 
                          variant={integration.status === "connected" ? "default" : "destructive"}
                          className="ml-2"
                        >
                          {integration.status}
                        </Badge>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Content to Publish</Label>
              <Select value={publishContentType} onValueChange={setPublishContentType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="titles">Titles only</SelectItem>
                  <SelectItem value="descriptions">Meta descriptions only</SelectItem>
                  <SelectItem value="both">Both titles and descriptions</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="dry-run"
                checked={isDryRun}
                onCheckedChange={setIsDryRun}
              />
              <Label htmlFor="dry-run">Dry run (test without making changes)</Label>
            </div>

            {selectedIntegration && (
              <div className="p-3 bg-muted rounded-lg">
                <div className="text-sm">
                  <div className="font-medium">Integration Details:</div>
                  <div className="text-muted-foreground">
                    Plugin: {wpIntegrations.find(i => i.id === selectedIntegration)?.plugin_type}
                  </div>
                </div>
              </div>
            )}

            <Button onClick={handlePublishToWordPress} className="w-full">
              <Upload className="mr-2 h-4 w-4" />
              {isDryRun ? "Test Publish" : "Publish to WordPress"}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Recent Jobs */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Export & Publishing Jobs</CardTitle>
          <CardDescription>
            Track the status of your recent export and publishing operations.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {exportJobs.map((job) => (
              <div key={job.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(job.status)}
                  <div>
                    <div className="font-medium">
                      {job.type === "csv_export" ? "CSV Export" : "WordPress Publish"} - {job.site_name}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {new Date(job.created_at).toLocaleString()}
                      {job.row_count && ` • ${job.row_count} rows`}
                    </div>
                    {job.error_message && (
                      <div className="text-sm text-red-600">{job.error_message}</div>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant={getStatusColor(job.status) as any}>
                    {job.status}
                  </Badge>
                  {job.status === "completed" && job.type === "csv_export" && (
                    <Button variant="ghost" size="sm">
                      <Download className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* WordPress Integrations Management */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            WordPress Integrations
            <Button variant="outline" size="sm">
              <Settings className="mr-2 h-4 w-4" />
              Manage Integrations
            </Button>
          </CardTitle>
          <CardDescription>
            Configure and manage your WordPress site connections.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {wpIntegrations.map((integration) => (
              <div key={integration.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <div className="font-medium">{integration.site_name}</div>
                  <div className="text-sm text-muted-foreground">
                    {integration.wp_url} • {integration.plugin_type} plugin
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant={integration.status === "connected" ? "default" : "destructive"}>
                    {integration.status}
                  </Badge>
                  <Button variant="ghost" size="sm">
                    <Settings className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
