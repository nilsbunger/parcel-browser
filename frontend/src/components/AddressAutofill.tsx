import React from "react";
import { AddressAutofill } from "@mapbox/search-js-react";

export function Component() {
  const [value, setValue] = React.useState('');
  return (
    <form>
      <AddressAutofill accessToken={<your access token here>}>
      <input
        autoComplete="shipping address-line1"
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />
    </AddressAutofill>
</form>
)

    }