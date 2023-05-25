import React from "react"
import ReactDOM from "react-dom"

import { MantineProvider } from "@mantine/core"
import { MyRoutes } from "../Routes"
import { AuthProvider } from "../hooks/Auth"
import { Notifications } from "@mantine/notifications"

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
ReactDOM.render(<App />, app)
