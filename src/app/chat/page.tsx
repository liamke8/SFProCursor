"use client"

import { useState, useRef, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { Send, Bot, User, ExternalLink, Copy, Sparkles } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useToast } from "@/hooks/use-toast"

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: Array<{
    url: string
    title: string
    excerpt: string
    relevance_score: number
  }>
  suggestions?: string[]
  tools_used?: string[]
}

interface Site {
  id: string
  name: string
  domain: string
}

// Mock sites data
const mockSites: Site[] = [
  { id: "site-1", name: "Example Company", domain: "example.com" },
  { id: "site-2", name: "Blog Site", domain: "blog.example.com" },
  { id: "site-3", name: "E-commerce Store", domain: "store.example.com" },
]

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Hi! I'm your SEO assistant. I can help you analyze your website, identify optimization opportunities, and answer questions about your content. What would you like to know?",
      timestamp: new Date(),
      suggestions: [
        "Show me pages with missing titles",
        "What are my biggest SEO issues?",
        "How can I improve my content quality?",
        "Find pages with thin content"
      ]
    }
  ])
  const [inputValue, setInputValue] = useState("")
  const [selectedSite, setSelectedSite] = useState<string>("")
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { toast } = useToast()

  // In a real app, this would fetch from the API
  const { data: sites = [] } = useQuery({
    queryKey: ["sites"],
    queryFn: async () => {
      await new Promise(resolve => setTimeout(resolve, 500))
      return mockSites
    },
  })

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: inputValue,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue("")
    setIsLoading(true)

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000))

      // Mock response based on user input
      const response = generateMockResponse(inputValue, selectedSite)
      
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.message,
        timestamp: new Date(),
        sources: response.sources,
        suggestions: response.suggestions,
        tools_used: response.tools_used
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to send message. Please try again.",
        variant: "destructive"
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setInputValue(suggestion)
  }

  const handleCopyMessage = (content: string) => {
    navigator.clipboard.writeText(content)
    toast({
      title: "Copied",
      description: "Message copied to clipboard"
    })
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="container mx-auto py-6 h-screen flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">SEO Chat Agent</h1>
          <p className="text-muted-foreground">
            Get AI-powered SEO insights and recommendations for your website.
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="w-64">
            <Select value={selectedSite} onValueChange={setSelectedSite}>
              <SelectTrigger>
                <SelectValue placeholder="Select a site..." />
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
        </div>
      </div>

      {/* Chat Container */}
      <Card className="flex-1 flex flex-col">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            Chat Assistant
            {selectedSite && (
              <Badge variant="secondary">
                {sites.find(s => s.id === selectedSite)?.domain}
              </Badge>
            )}
          </CardTitle>
          <CardDescription>
            Ask questions about your SEO performance, get optimization recommendations, or request specific analyses.
          </CardDescription>
        </CardHeader>
        
        <CardContent className="flex-1 flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto space-y-4 mb-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex gap-3 max-w-[80%] ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                  {/* Avatar */}
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                    message.role === 'user' 
                      ? 'bg-primary text-primary-foreground' 
                      : 'bg-secondary text-secondary-foreground'
                  }`}>
                    {message.role === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                  </div>

                  {/* Message Content */}
                  <div className={`space-y-2 ${message.role === 'user' ? 'text-right' : 'text-left'}`}>
                    <div className={`inline-block p-3 rounded-lg ${
                      message.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    }`}>
                      <div className="whitespace-pre-wrap">{message.content}</div>
                      
                      {/* Tools Used */}
                      {message.tools_used && message.tools_used.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {message.tools_used.map((tool, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              <Sparkles className="h-3 w-3 mr-1" />
                              {tool}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Sources */}
                    {message.sources && message.sources.length > 0 && (
                      <div className="space-y-2">
                        <div className="text-sm font-medium text-muted-foreground">Sources:</div>
                        <div className="space-y-1">
                          {message.sources.slice(0, 3).map((source, idx) => (
                            <div key={idx} className="text-sm border rounded p-2 bg-background">
                              <div className="flex items-center justify-between">
                                <div className="font-medium truncate">{source.title}</div>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 w-6 p-0"
                                  onClick={() => window.open(source.url, '_blank')}
                                >
                                  <ExternalLink className="h-3 w-3" />
                                </Button>
                              </div>
                              <div className="text-muted-foreground text-xs mt-1">{source.excerpt}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Suggestions */}
                    {message.suggestions && message.suggestions.length > 0 && (
                      <div className="space-y-2">
                        <div className="text-sm font-medium text-muted-foreground">Try asking:</div>
                        <div className="flex flex-wrap gap-2">
                          {message.suggestions.map((suggestion, idx) => (
                            <Button
                              key={idx}
                              variant="outline"
                              size="sm"
                              className="text-xs"
                              onClick={() => handleSuggestionClick(suggestion)}
                            >
                              {suggestion}
                            </Button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Message Actions */}
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{message.timestamp.toLocaleTimeString()}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={() => handleCopyMessage(message.content)}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
            
            {/* Loading Message */}
            {isLoading && (
              <div className="flex gap-3 justify-start">
                <div className="w-8 h-8 rounded-full bg-secondary text-secondary-foreground flex items-center justify-center">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="bg-muted p-3 rounded-lg">
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="flex gap-2">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about your SEO performance..."
              disabled={isLoading}
              className="flex-1"
            />
            <Button 
              onClick={handleSendMessage} 
              disabled={!inputValue.trim() || isLoading}
              size="icon"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Mock response generator
function generateMockResponse(input: string, siteId?: string): {
  message: string
  sources?: Array<{url: string, title: string, excerpt: string, relevance_score: number}>
  suggestions?: string[]
  tools_used?: string[]
} {
  const inputLower = input.toLowerCase()
  
  if (inputLower.includes('missing') && inputLower.includes('title')) {
    return {
      message: `I found 23 pages with missing title tags on your website. This is a critical SEO issue that should be addressed immediately.\n\nThe pages missing titles include:\n- /about-us\n- /contact\n- /blog/post-1\n- /products/category-a\n\nMissing title tags prevent search engines from understanding your page content and can significantly hurt your search rankings. I recommend generating titles for these pages using our AI templates.`,
      sources: [
        {
          url: "https://example.com/about-us",
          title: "About Us - No Title",
          excerpt: "Learn more about our company history and mission...",
          relevance_score: 0.95
        },
        {
          url: "https://example.com/contact",
          title: "Contact - No Title", 
          excerpt: "Get in touch with our team for support...",
          relevance_score: 0.87
        }
      ],
      suggestions: [
        "Generate titles for these pages",
        "Show me pages with missing descriptions too",
        "What's the SEO impact of missing titles?"
      ],
      tools_used: ["site_search", "seo_analysis"]
    }
  }
  
  if (inputLower.includes('seo') && inputLower.includes('issue')) {
    return {
      message: `Based on my analysis of your website, here are the top SEO issues I've identified:\n\n**Critical Issues:**\n• 23 pages missing title tags\n• 45 pages missing meta descriptions\n• 12 pages with thin content (<300 words)\n\n**Technical Issues:**\n• 5 pages returning 404 errors\n• Slow loading times on mobile\n• Missing alt text on 67 images\n\n**Content Issues:**\n• Duplicate content on 8 pages\n• Poor internal linking structure\n• Inconsistent heading hierarchy\n\nI recommend starting with the title tags and meta descriptions as they have the highest impact on search rankings.`,
      suggestions: [
        "Fix missing title tags first",
        "Generate meta descriptions in bulk",
        "Show me the thin content pages",
        "How do I improve page load speed?"
      ],
      tools_used: ["site_analysis", "technical_audit"]
    }
  }
  
  if (inputLower.includes('content') && inputLower.includes('quality')) {
    return {
      message: `I've analyzed your content quality across ${siteId ? 'this site' : 'all your sites'}. Here's what I found:\n\n**Content Statistics:**\n• Average word count: 487 words\n• 12 pages under 300 words (thin content)\n• Reading level: 8th grade (good for accessibility)\n• Keyword density: Optimized on 68% of pages\n\n**Recommendations:**\n1. Expand thin content pages to at least 500 words\n2. Add more internal links between related pages\n3. Include more visual content (images, videos)\n4. Optimize for featured snippets with FAQ sections\n\nPages that need the most attention:\n• /services (247 words)\n• /pricing (193 words)\n• /features (289 words)`,
      sources: [
        {
          url: "https://example.com/services",
          title: "Our Services",
          excerpt: "We offer a range of services including...",
          relevance_score: 0.91
        }
      ],
      suggestions: [
        "Expand thin content pages",
        "Add FAQ sections to key pages",
        "Improve internal linking",
        "Optimize for featured snippets"
      ],
      tools_used: ["content_analysis", "readability_check"]
    }
  }
  
  // Default response
  return {
    message: `I understand you're asking about "${input}". I can help you with various SEO tasks including:\n\n• Analyzing page performance and identifying issues\n• Finding optimization opportunities\n• Generating SEO-optimized content\n• Technical SEO audits\n• Content gap analysis\n\nCould you be more specific about what you'd like me to help you with?`,
    suggestions: [
      "Show me my biggest SEO issues",
      "Find pages with missing titles",
      "Analyze my content quality",
      "Check for technical problems"
    ],
    tools_used: ["general_analysis"]
  }
}
