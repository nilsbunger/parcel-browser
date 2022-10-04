
import { MantineProvider } from '@mantine/core';
import React = require('react');
import { MyRoutes } from "./Routes";

export function App() {
  return (
    <MantineProvider withGlobalStyles withNormalizeCSS>
      <MyRoutes />
    </MantineProvider>
  );
}
