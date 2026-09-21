import type { Metadata, Viewport } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'LegalAid AI — Accessible Legal Information',
  description: 'AI-powered legal information platform providing plain-language guidance on legal questions. Not legal advice.',
  keywords: ['legal information', 'legal aid', 'AI', 'access to justice', 'legal guidance'],
  authors: [{ name: 'LegalAid AI Team' }],
  openGraph: {
    title: 'LegalAid AI',
    description: 'Accessible legal information powered by AI',
    type: 'website',
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#2563eb',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="antialiased text-gray-900 bg-gray-50">
        {children}
      </body>
    </html>
  );
}