'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Bot, 
  Search, 
  FileText, 
  BarChart, 
  Download, 
  Upload,
  Globe,
  Zap,
  Users,
  ChevronRight
} from 'lucide-react'

export default function HomePage() {
  const [stats] = useState({
    totalSites: 5,
    pagesIndexed: 1247,
    aiOptimizations: 89,
    publishedPages: 67
  })

  const features = [
    {
      icon: Search,
      title: "Smart Web Crawler",
      description: "JavaScript rendering with bot detection workarounds. Full or directed crawls.",
      status: "active"
    },
    {
      icon: Bot,
      title: "AI Content Processing", 
      description: "30+ SEO prompt templates with GPT-4, Claude, and local models.",
      status: "active"
    },
    {
      icon: FileText,
      title: "Spreadsheet Interface",
      description: "Filter, sort, and bulk optimize pages with advanced table operations.",
      status: "active"
    },
    {
      icon: BarChart,
      title: "SEO Chat Agent",
      description: "Site-aware AI assistant with built-in SEO tools and recommendations.",
      status: "coming-soon"
    },
    {
      icon: Download,
      title: "Export & Publishing",
      description: "CSV exports and WordPress integration with major SEO plugin support.",
      status: "active"
    },
    {
      icon: Upload,
      title: "Multi-tenant Management",
      description: "Organizations, teams, and role-based access control.",
      status: "active"
    }
  ]

  const quickActions = [
    {
      title: "Add New Site",
      description: "Connect a website for crawling and optimization",
      icon: Globe,
      href: "/sites/new"
    },
    {
      title: "Start Crawl",
      description: "Begin crawling pages to extract SEO data",
      icon: Search,
      href: "/crawls/new"
    },
    {
      title: "Run AI Optimization",
      description: "Apply prompt templates to generate optimized content",
      icon: Zap,
      href: "/runs/new"
    },
    {
      title: "Chat with Agent",
      description: "Get SEO insights and recommendations",
      icon: Bot,
      href: "/chat"
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            SEO Automation Platform
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            AI-powered SEO optimization at scale. Crawl websites, process content with AI, 
            manage optimizations in spreadsheet-like tables, and publish results.
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Sites</CardTitle>
              <Globe className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalSites}</div>
              <p className="text-xs text-muted-foreground">Connected websites</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pages Indexed</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.pagesIndexed.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">Crawled and processed</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">AI Optimizations</CardTitle>
              <Bot className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.aiOptimizations}</div>
              <p className="text-xs text-muted-foreground">Generated this month</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Published</CardTitle>
              <Upload className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.publishedPages}</div>
              <p className="text-xs text-muted-foreground">Pages updated</p>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {quickActions.map((action, index) => (
              <Card key={index} className="cursor-pointer hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-center space-x-4">
                    <div className="p-2 bg-primary/10 rounded-lg">
                      <action.icon className="h-6 w-6 text-primary" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{action.title}</h3>
                      <p className="text-sm text-gray-600 mt-1">{action.description}</p>
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-400" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Features Grid */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Platform Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <Card key={index}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="p-2 bg-primary/10 rounded-lg">
                      <feature.icon className="h-6 w-6 text-primary" />
                    </div>
                    <Badge 
                      variant={feature.status === 'active' ? 'default' : 'secondary'}
                    >
                      {feature.status === 'active' ? 'Active' : 'Coming Soon'}
                    </Badge>
                  </div>
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>{feature.description}</CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Getting Started */}
        <Card className="bg-gradient-to-r from-blue-500 to-purple-600 text-white">
          <CardContent className="p-8">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold mb-2">Ready to Get Started?</h2>
                <p className="text-blue-100 mb-4">
                  Connect your first website and start optimizing with AI-powered SEO tools.
                </p>
                <div className="flex space-x-4">
                  <Button variant="secondary" size="lg">
                    <Globe className="mr-2 h-4 w-4" />
                    Add First Site
                  </Button>
                  <Button variant="outline" size="lg" className="bg-transparent border-white text-white hover:bg-white/10">
                    <FileText className="mr-2 h-4 w-4" />
                    View Documentation
                  </Button>
                </div>
              </div>
              <div className="hidden lg:block">
                <Users className="h-24 w-24 text-blue-200" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
