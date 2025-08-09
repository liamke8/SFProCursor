import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { ClerkProvider } from '@clerk/nextjs'
import { Toaster } from '@/components/ui/toaster'
import { AppProvider } from '@/providers/app-provider'
import { Navigation } from '@/components/layout/navigation'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'SEO Automation Platform',
  description: 'AI-powered SEO automation platform for content optimization at scale',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body className={inter.className}>
          <AppProvider>
            <Navigation>
              {children}
            </Navigation>
            <Toaster />
          </AppProvider>
        </body>
      </html>
    </ClerkProvider>
  )
}
