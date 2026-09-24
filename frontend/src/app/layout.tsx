import type { Metadata, Viewport } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: {
    default: 'LegalAI Access — Safer Legal Information for Everyone',
    template: '%s | LegalAI Access',
  },
  description: 'Get structured, jurisdiction-aware legal guidance powered by AI with deterministic no-API fallback. Not legal advice.',
  keywords: ['legal information', 'legal aid', 'AI', 'access to justice', 'legal guidance', 'deterministic legal'],
  authors: [{ name: 'LegalAI Access Team' }],
  openGraph: {
    title: 'LegalAI Access — Safer Legal Information for Everyone',
    description: 'Accessible legal information powered by AI with deterministic fallback',
    type: 'website',
    siteName: 'LegalAI Access',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'LegalAI Access',
    description: 'Structured legal information with no API key required',
  },
  robots: {
    index: true,
    follow: true,
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
        <style
          dangerouslySetInnerHTML={{
            __html: `
              @media (prefers-reduced-motion: reduce) {
                *, *::before, *::after {
                  animation-duration: 0.01ms !important;
                  animation-iteration-count: 1 !important;
                  transition-duration: 0.01ms !important;
                }
              }
              .animate-slide-up {
                animation: slideUp 0.3s ease-out;
              }
              @keyframes slideUp {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
              }
            `,
          }}
        />
      </head>
      <body className="antialiased text-gray-900 bg-gray-50">
        {children}
      </body>
    </html>
  );
}