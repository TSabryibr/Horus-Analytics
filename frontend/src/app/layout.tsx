import type { Metadata } from "next";
import "./globals.css";
import BootLayoutGate from "./components/BootLayoutGate";
import MainLayoutWrapper from "./components/MainLayoutWrapper";
import PageTransition from "../components/PageTransition";
import { GlobalDataProvider } from "./context/GlobalDataContext";
import { LanguageProvider } from "../context/LanguageContext";

export const metadata: Metadata = {
  title: "Horus Analytics",
  description: "Institutional Trading Terminal",
  icons: {
    icon: [
      { url: '/favicon.ico' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
      { url: '/android-chrome-192x192.png', sizes: '192x192', type: 'image/png' },
    ],
    shortcut: '/favicon.ico',
    apple: '/apple-touch-icon.png',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-sans antialiased" suppressHydrationWarning>
        <LanguageProvider>
          <BootLayoutGate>
            <GlobalDataProvider>
              <MainLayoutWrapper>
                <PageTransition>
                  {children}
                </PageTransition>
              </MainLayoutWrapper>
            </GlobalDataProvider>
          </BootLayoutGate>
        </LanguageProvider>
      </body>
    </html>
  );
}
