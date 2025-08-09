"use client"

import { ColumnDef } from "@tanstack/react-table"
import { ArrowUpDown, MoreHorizontal, ExternalLink, Edit, Eye } from "lucide-react"
import Link from "next/link"

import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Badge } from "@/components/ui/badge"
import { formatDate, truncateText, getStatusColor } from "@/lib/utils"

export type Page = {
  id: string
  site_id: string
  url: string
  status_code: number | null
  canonical: string | null
  meta_robots: string | null
  word_count: number
  last_crawled_at: string
  title: string | null
  description: string | null
  h1: string | null
  h2_json: string[] | null
  // Computed fields
  missing_title: boolean
  missing_description: boolean
  title_length: number
  description_length: number
  has_duplicates: boolean
}

export const columns: ColumnDef<Page>[] = [
  {
    id: "select",
    header: ({ table }) => (
      <Checkbox
        checked={table.getIsAllPageRowsSelected()}
        onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
        aria-label="Select all"
      />
    ),
    cell: ({ row }) => (
      <Checkbox
        checked={row.getIsSelected()}
        onCheckedChange={(value) => row.toggleSelected(!!value)}
        aria-label="Select row"
      />
    ),
    enableSorting: false,
    enableHiding: false,
  },
  {
    accessorKey: "url",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="h-8 p-0 hover:bg-transparent"
        >
          URL
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      const url = row.getValue("url") as string
      return (
        <div className="flex items-center space-x-2">
          <Link
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-blue-600 hover:text-blue-800 hover:underline max-w-xs truncate"
            title={url}
          >
            {truncateText(url, 50)}
          </Link>
          <ExternalLink className="h-3 w-3 text-gray-400" />
        </div>
      )
    },
  },
  {
    accessorKey: "status_code",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="h-8 p-0 hover:bg-transparent"
        >
          Status
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      const status = row.getValue("status_code") as number | null
      if (!status) return <span className="text-gray-400">-</span>
      
      let variant: "default" | "secondary" | "destructive" = "default"
      if (status >= 400) variant = "destructive"
      else if (status >= 300) variant = "secondary"
      
      return <Badge variant={variant}>{status}</Badge>
    },
  },
  {
    accessorKey: "title",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="h-8 p-0 hover:bg-transparent"
        >
          Title
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      const title = row.getValue("title") as string | null
      const missing = !title || title.trim() === ""
      
      if (missing) {
        return <Badge variant="destructive">Missing</Badge>
      }
      
      return (
        <div className="max-w-xs">
          <div 
            className="font-medium truncate" 
            title={title}
          >
            {truncateText(title, 40)}
          </div>
          <div className="text-xs text-gray-500">
            {title.length} chars
          </div>
        </div>
      )
    },
  },
  {
    accessorKey: "description",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="h-8 p-0 hover:bg-transparent"
        >
          Description
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      const description = row.getValue("description") as string | null
      const missing = !description || description.trim() === ""
      
      if (missing) {
        return <Badge variant="destructive">Missing</Badge>
      }
      
      return (
        <div className="max-w-xs">
          <div 
            className="text-sm truncate" 
            title={description}
          >
            {truncateText(description, 50)}
          </div>
          <div className="text-xs text-gray-500">
            {description.length} chars
          </div>
        </div>
      )
    },
  },
  {
    accessorKey: "h1",
    header: "H1",
    cell: ({ row }) => {
      const h1 = row.getValue("h1") as string | null
      
      if (!h1 || h1.trim() === "") {
        return <Badge variant="destructive">Missing</Badge>
      }
      
      return (
        <div className="max-w-xs truncate font-medium" title={h1}>
          {truncateText(h1, 30)}
        </div>
      )
    },
  },
  {
    accessorKey: "word_count",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="h-8 p-0 hover:bg-transparent"
        >
          Words
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      const count = row.getValue("word_count") as number
      
      let variant: "default" | "secondary" | "destructive" = "default"
      if (count < 300) variant = "destructive"
      else if (count < 600) variant = "secondary"
      
      return <Badge variant={variant}>{count.toLocaleString()}</Badge>
    },
  },
  {
    accessorKey: "last_crawled_at",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="h-8 p-0 hover:bg-transparent"
        >
          Last Crawled
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      const date = row.getValue("last_crawled_at") as string
      return (
        <div className="text-sm text-gray-600">
          {formatDate(new Date(date))}
        </div>
      )
    },
  },
  {
    id: "issues",
    header: "Issues",
    cell: ({ row }) => {
      const issues = []
      
      if (!row.getValue("title")) issues.push("No title")
      if (!row.getValue("description")) issues.push("No description")
      if (!row.getValue("h1")) issues.push("No H1")
      if ((row.getValue("word_count") as number) < 300) issues.push("Thin content")
      
      if (issues.length === 0) {
        return <Badge variant="default">Good</Badge>
      }
      
      return (
        <div className="flex flex-wrap gap-1">
          {issues.slice(0, 2).map((issue, idx) => (
            <Badge key={idx} variant="destructive" className="text-xs">
              {issue}
            </Badge>
          ))}
          {issues.length > 2 && (
            <Badge variant="secondary" className="text-xs">
              +{issues.length - 2} more
            </Badge>
          )}
        </div>
      )
    },
  },
  {
    id: "actions",
    enableHiding: false,
    cell: ({ row }) => {
      const page = row.original

      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">Open menu</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Actions</DropdownMenuLabel>
            <DropdownMenuItem
              onClick={() => navigator.clipboard.writeText(page.url)}
            >
              Copy URL
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href={`/pages/${page.id}`}>
                <Eye className="mr-2 h-4 w-4" />
                View Details
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href={`/pages/${page.id}/edit`}>
                <Edit className="mr-2 h-4 w-4" />
                Edit SEO
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href={page.url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="mr-2 h-4 w-4" />
                Visit Page
              </Link>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )
    },
  },
]
