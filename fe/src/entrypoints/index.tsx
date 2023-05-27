import React from "react"

import { MantineProvider } from "@mantine/core"
import { MyRoutes } from "../Routes"
import { AuthProvider } from "../hooks/Auth"
import { Notifications } from "@mantine/notifications"
import { createRoot } from "react-dom/client";

export function App() {
  return (
    <MantineProvider>
      <Notifications position="top-right" zIndex={2077} limit={8} />
      <AuthProvider>
        <MyRoutes />
      </AuthProvider>
    </MantineProvider>
  )
}

const app = document.getElementById("app")
// eslint-disable-next-line @typescript-eslint/no-non-null-assertion
const root = createRoot(app!);
root.render(<App />);
