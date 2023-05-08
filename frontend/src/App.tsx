import { MantineProvider } from "@mantine/core"
import { MyRoutes } from "./Routes"
import { AuthProvider } from "./hooks/Auth"
import React from "react"
import { Notifications } from "@mantine/notifications"

export function App() {
  return (
    <MantineProvider withGlobalStyles withNormalizeCSS>
      <Notifications position="top-right" zIndex={2077} limit={8} />
      <AuthProvider>
        <MyRoutes />
      </AuthProvider>
    </MantineProvider>
  )
}
