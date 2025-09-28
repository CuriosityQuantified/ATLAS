import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import CopilotProvider from '../components/CopilotProvider'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'ATLAS - Agentic Task Logic & Analysis System',
  description: 'Multi-agent reasoning system for strategic analysis and content generation',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <CopilotProvider>
          {children}
        </CopilotProvider>
      </body>
    </html>
  )
}