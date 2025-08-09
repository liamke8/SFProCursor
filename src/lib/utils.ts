import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: Date | string): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(dateObj)
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'completed':
    case 'success':
      return 'text-green-600'
    case 'failed':
    case 'error':
      return 'text-red-600'
    case 'pending':
    case 'running':
      return 'text-yellow-600'
    default:
      return 'text-gray-600'
  }
}