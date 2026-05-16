import { AppStateProvider } from "@/components/app-state-provider"

export default function ExperienceLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return <AppStateProvider>{children}</AppStateProvider>
}
