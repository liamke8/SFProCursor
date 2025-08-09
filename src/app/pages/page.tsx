"use client"

import { useState, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { Plus, RefreshCw } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { DataTable } from "@/components/data-table/data-table"
import { columns, type Page } from "@/components/pages/columns"
import { BulkActions } from "@/components/pages/bulk-actions"
import { Filters, type FilterValue } from "@/components/pages/filters"
import { useToast } from "@/hooks/use-toast"

// Mock data for development
const mockPages: Page[] = [
  {
    id: "1",
    site_id: "site-1",
    url: "https://example.com/",
    status_code: 200,
    canonical: "https://example.com/",
    meta_robots: "index, follow",
    word_count: 1250,
    last_crawled_at: "2024-01-15T10:30:00Z",
    title: "Home - Example Company | Leading SEO Solutions",
    description: "Discover powerful SEO solutions that help businesses grow online. Our comprehensive platform offers everything you need to improve your search rankings.",
    h1: "Welcome to Example Company",
    h2_json: ["Our Services", "Why Choose Us", "Get Started Today"],
    missing_title: false,
    missing_description: false,
    title_length: 52,
    description_length: 147,
    has_duplicates: false,
  },
  {
    id: "2", 
    site_id: "site-1",
    url: "https://example.com/about",
    status_code: 200,
    canonical: "https://example.com/about",
    meta_robots: "index, follow",
    word_count: 890,
    last_crawled_at: "2024-01-15T10:31:00Z",
    title: null,
    description: null,
    h1: "About Our Company",
    h2_json: ["Our Mission", "Team"],
    missing_title: true,
    missing_description: true,
    title_length: 0,
    description_length: 0,
    has_duplicates: false,
  },
  {
    id: "3",
    site_id: "site-1", 
    url: "https://example.com/blog/seo-guide",
    status_code: 200,
    canonical: "https://example.com/blog/seo-guide",
    meta_robots: "index, follow",
    word_count: 3200,
    last_crawled_at: "2024-01-15T10:32:00Z",
    title: "The Ultimate SEO Guide for 2024",
    description: "Learn the latest SEO strategies and techniques that actually work in 2024. Complete guide with actionable tips.",
    h1: "SEO Guide 2024",
    h2_json: ["Technical SEO", "Content Strategy", "Link Building", "Analytics"],
    missing_title: false,
    missing_description: false,
    title_length: 33,
    description_length: 108,
    has_duplicates: false,
  },
  {
    id: "4",
    site_id: "site-1",
    url: "https://example.com/pricing", 
    status_code: 200,
    canonical: "https://example.com/pricing",
    meta_robots: "index, follow",
    word_count: 650,
    last_crawled_at: "2024-01-15T10:33:00Z",
    title: "Pricing Plans - Affordable SEO Solutions for Every Business Size and Budget Range",
    description: "Choose from our flexible pricing plans designed for businesses of all sizes. Get started with our free plan or upgrade for premium features and priority support.",
    h1: "Pricing Plans",
    h2_json: ["Free Plan", "Pro Plan", "Enterprise"],
    missing_title: false,
    missing_description: false,
    title_length: 89,
    description_length: 161,
    has_duplicates: false,
  },
  {
    id: "5",
    site_id: "site-1",
    url: "https://example.com/contact",
    status_code: 404,
    canonical: null,
    meta_robots: null,
    word_count: 0,
    last_crawled_at: "2024-01-15T10:34:00Z",
    title: null,
    description: null,
    h1: null,
    h2_json: null,
    missing_title: true,
    missing_description: true,
    title_length: 0,
    description_length: 0,
    has_duplicates: false,
  },
]

export default function PagesPage() {
  const [selectedPages, setSelectedPages] = useState<Page[]>([])
  const [filters, setFilters] = useState<FilterValue[]>([])
  const { toast } = useToast()

  // In a real app, this would fetch from the API
  const { data: pages = [], isLoading, refetch } = useQuery({
    queryKey: ["pages", filters],
    queryFn: async () => {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Apply filters to mock data
      let filteredPages = mockPages
      
      filters.forEach(filter => {
        filteredPages = filteredPages.filter(page => {
          const value = page[filter.key as keyof Page]
          
          switch (filter.operator) {
            case "equals":
              return value === filter.value
            case "contains":
              return String(value).toLowerCase().includes(String(filter.value).toLowerCase())
            case "greater_than":
              return Number(value) > Number(filter.value)
            case "less_than":
              return Number(value) < Number(filter.value)
            default:
              return true
          }
        })
      })
      
      return filteredPages
    },
  })

  const handleRunPrompt = async (templateId: string, pageIds: string[]) => {
    toast({
      title: "AI Run Started",
      description: `Running template on ${pageIds.length} pages. This may take a few minutes.`,
    })
    
    // In a real app, this would call the API
    console.log("Running prompt:", { templateId, pageIds })
  }

  const handleExport = async (pageIds: string[]) => {
    toast({
      title: "Export Started", 
      description: `Exporting ${pageIds.length} pages to CSV.`,
    })
    
    // In a real app, this would trigger CSV download
    console.log("Exporting pages:", pageIds)
  }

  const handlePublish = async (pageIds: string[]) => {
    toast({
      title: "Publishing Started",
      description: `Queuing ${pageIds.length} pages for WordPress publishing.`,
    })
    
    // In a real app, this would call the publishing API
    console.log("Publishing pages:", pageIds)
  }

  const stats = {
    total: pages.length,
    missingTitle: pages.filter(p => p.missing_title).length,
    missingDescription: pages.filter(p => p.missing_description).length,
    thinContent: pages.filter(p => p.word_count < 300).length,
    errors: pages.filter(p => p.status_code && p.status_code >= 400).length,
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Pages</h1>
          <p className="text-muted-foreground">
            Manage and optimize your website pages with AI-powered SEO tools.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isLoading}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button size="sm">
            <Plus className="mr-2 h-4 w-4" />
            Start Crawl
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Pages</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-muted-foreground">All crawled pages</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Missing Titles</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.missingTitle}</div>
            <p className="text-xs text-muted-foreground">Pages without titles</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Missing Descriptions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.missingDescription}</div>
            <p className="text-xs text-muted-foreground">Pages without meta descriptions</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Thin Content</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{stats.thinContent}</div>
            <p className="text-xs text-muted-foreground">{"< 300 words"}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Errors</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.errors}</div>
            <p className="text-xs text-muted-foreground">4xx/5xx status codes</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Pages</CardTitle>
          <CardDescription>
            Filter, sort, and perform bulk operations on your pages.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={columns}
            data={pages}
            searchKey="url"
            onSelectionChange={setSelectedPages}
            filters={
              <Filters 
                filters={filters}
                onFiltersChange={setFilters}
              />
            }
            bulkActions={
              <BulkActions
                selectedPages={selectedPages}
                onRunPrompt={handleRunPrompt}
                onExport={handleExport}
                onPublish={handlePublish}
              />
            }
          />
        </CardContent>
      </Card>
    </div>
  )
}
