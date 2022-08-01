import React from 'react';
import Home3LogoIcon from 'jsx:./Home3LogoIcon.svg';

export default function Home3Logo() {
  return (
    <>
      <div className="flex items-center">
        <Home3LogoIcon style={{ height: '32px' }} />
        <p className="font-heading text-3xl font-bold text-slate-800 ml-2">
          Home3
        </p>
      </div>
    </>
  );
}
