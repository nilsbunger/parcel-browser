import * as React from 'react';
import Home3Logo from "./Home3Logo";

export default function Splashscreen({ msg }) {
  return (
    <div className="h-screen w-screen coolbg">
      <div className="h-screen w-screen flex flex-col justify-center items-center scale-150">
        <Home3Logo />
        <p className="text-sm py-3">{msg}</p>
      </div>
    </div>
  );
}
