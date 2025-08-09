"use client"

import { useState } from "react"
import { Filter, X, ChevronDown } from "lucide-react"

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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

export interface FilterValue {
  key: string
  operator: string
  value: string | number
  label: string
}

interface FiltersProps {
  filters: FilterValue[]
  onFiltersChange: (filters: FilterValue[]) => void
}

const filterDefinitions = [
  {
    key: "status_code",
    label: "Status Code",
    type: "select",
    options: [
      { value: "200", label: "200 (OK)" },
      { value: "301", label: "301 (Redirect)" },
      { value: "302", label: "302 (Redirect)" },
      { value: "404", label: "404 (Not Found)" },
      { value: "500", label: "500 (Error)" },
    ],
  },
  {
    key: "missing_title",
    label: "Missing Title",
    type: "boolean",
    operators: ["equals"],
  },
  {
    key: "missing_description",
    label: "Missing Description", 
    type: "boolean",
    operators: ["equals"],
  },
  {
    key: "missing_h1",
    label: "Missing H1",
    type: "boolean",
    operators: ["equals"],
  },
  {
    key: "word_count",
    label: "Word Count",
    type: "number",
    operators: ["equals", "greater_than", "less_than", "between"],
  },
  {
    key: "title_length",
    label: "Title Length",
    type: "number",
    operators: ["equals", "greater_than", "less_than", "between"],
  },
  {
    key: "description_length",
    label: "Description Length",
    type: "number", 
    operators: ["equals", "greater_than", "less_than", "between"],
  },
  {
    key: "url",
    label: "URL Contains",
    type: "text",
    operators: ["contains", "starts_with", "ends_with"],
  },
  {
    key: "last_crawled_at",
    label: "Last Crawled",
    type: "date",
    operators: ["after", "before", "between"],
  },
]

const operators = {
  equals: "Equals",
  greater_than: "Greater than",
  less_than: "Less than",
  between: "Between",
  contains: "Contains",
  starts_with: "Starts with",
  ends_with: "Ends with",
  after: "After",
  before: "Before",
}

export function Filters({ filters, onFiltersChange }: FiltersProps) {
  const [isAddingFilter, setIsAddingFilter] = useState(false)
  const [newFilter, setNewFilter] = useState<Partial<FilterValue>>({})

  const addFilter = () => {
    if (newFilter.key && newFilter.operator && newFilter.value !== undefined) {
      const filterDef = filterDefinitions.find(f => f.key === newFilter.key)
      const filter: FilterValue = {
        key: newFilter.key,
        operator: newFilter.operator,
        value: newFilter.value,
        label: `${filterDef?.label} ${operators[newFilter.operator as keyof typeof operators]} ${newFilter.value}`,
      }
      
      onFiltersChange([...filters, filter])
      setNewFilter({})
      setIsAddingFilter(false)
    }
  }

  const removeFilter = (index: number) => {
    const newFilters = filters.filter((_, i) => i !== index)
    onFiltersChange(newFilters)
  }

  const clearAllFilters = () => {
    onFiltersChange([])
  }

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {/* Active Filters */}
      {filters.map((filter, index) => (
        <Badge key={index} variant="secondary" className="gap-1">
          {filter.label}
          <Button
            variant="ghost"
            size="sm"
            className="h-4 w-4 p-0 hover:bg-transparent"
            onClick={() => removeFilter(index)}
          >
            <X className="h-3 w-3" />
          </Button>
        </Badge>
      ))}

      {/* Add Filter Dropdown */}
      <DropdownMenu open={isAddingFilter} onOpenChange={setIsAddingFilter}>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="h-8">
            <Filter className="mr-2 h-4 w-4" />
            Add Filter
            <ChevronDown className="ml-2 h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-80">
          <DropdownMenuLabel>Add Filter</DropdownMenuLabel>
          <DropdownMenuSeparator />
          
          <div className="p-2 space-y-3">
            {/* Field Selection */}
            <div>
              <label className="text-sm font-medium">Field</label>
              <Select
                value={newFilter.key}
                onValueChange={(value) => setNewFilter({ ...newFilter, key: value, operator: undefined, value: undefined })}
              >
                <SelectTrigger className="h-8 mt-1">
                  <SelectValue placeholder="Select field..." />
                </SelectTrigger>
                <SelectContent>
                  {filterDefinitions.map((field) => (
                    <SelectItem key={field.key} value={field.key}>
                      {field.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Operator Selection */}
            {newFilter.key && (
              <div>
                <label className="text-sm font-medium">Condition</label>
                <Select
                  value={newFilter.operator}
                  onValueChange={(value) => setNewFilter({ ...newFilter, operator: value, value: undefined })}
                >
                  <SelectTrigger className="h-8 mt-1">
                    <SelectValue placeholder="Select condition..." />
                  </SelectTrigger>
                  <SelectContent>
                    {(() => {
                      const field = filterDefinitions.find(f => f.key === newFilter.key)
                      const availableOperators = field?.operators || ["equals", "contains"]
                      
                      return availableOperators.map((op) => (
                        <SelectItem key={op} value={op}>
                          {operators[op as keyof typeof operators]}
                        </SelectItem>
                      ))
                    })()}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Value Input */}
            {newFilter.key && newFilter.operator && (
              <div>
                <label className="text-sm font-medium">Value</label>
                {(() => {
                  const field = filterDefinitions.find(f => f.key === newFilter.key)
                  
                  if (field?.type === "select") {
                    return (
                      <Select
                        value={newFilter.value as string}
                        onValueChange={(value) => setNewFilter({ ...newFilter, value })}
                      >
                        <SelectTrigger className="h-8 mt-1">
                          <SelectValue placeholder="Select value..." />
                        </SelectTrigger>
                        <SelectContent>
                          {field.options?.map((option) => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )
                  }
                  
                  if (field?.type === "boolean") {
                    return (
                      <Select
                        value={newFilter.value as string}
                        onValueChange={(value) => setNewFilter({ ...newFilter, value })}
                      >
                        <SelectTrigger className="h-8 mt-1">
                          <SelectValue placeholder="Select value..." />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="true">Yes</SelectItem>
                          <SelectItem value="false">No</SelectItem>
                        </SelectContent>
                      </Select>
                    )
                  }
                  
                  return (
                    <Input
                      type={field?.type === "number" ? "number" : "text"}
                      placeholder="Enter value..."
                      className="h-8 mt-1"
                      value={newFilter.value as string}
                      onChange={(e) => setNewFilter({ ...newFilter, value: e.target.value })}
                    />
                  )
                })()}
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setNewFilter({})
                  setIsAddingFilter(false)
                }}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={addFilter}
                disabled={!newFilter.key || !newFilter.operator || newFilter.value === undefined}
              >
                Add Filter
              </Button>
            </div>
          </div>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Clear All */}
      {filters.length > 0 && (
        <Button
          variant="ghost"
          size="sm"
          className="h-8 text-muted-foreground"
          onClick={clearAllFilters}
        >
          Clear all
        </Button>
      )}
    </div>
  )
}
