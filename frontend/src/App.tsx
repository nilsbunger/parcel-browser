import { MantineProvider } from '@mantine/core';
import { MyRoutes } from "./Routes";
import { AuthProvider } from "./hooks/Auth";
import { NotificationsProvider } from "@mantine/notifications";
import React from "react"

export function App() {
  return (
    <MantineProvider withGlobalStyles withNormalizeCSS>
      <NotificationsProvider position="top-right" zIndex={2077} limit={8}>
        <AuthProvider>
          <MyRoutes/>
        </AuthProvider>
      </NotificationsProvider>
    </MantineProvider>
  );
}
