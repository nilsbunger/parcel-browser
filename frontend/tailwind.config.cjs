module.exports = {
  darkMode: "unusedDarkModeClass", // disable dark mode for now. Remove to fallback to listening to prefer-media-scheme
  // Include Django template dirs (../*/templates/) so Tailwind can see classes used in Django templates.
  content: ["./src/**/*.{html,js,ts,tsx}", "../*/templates/**/*.html"],
  theme: {
    extend: {
      opacity: ["disabled"],
    },
    fontFamily: {
      accent: ["turboserif", "serif"],
      body: ["DM Sans", "sans-serif"],
    },
    container: {  // container parameters from tailwind docs
      center: true,
      padding: {
        DEFAULT: '1rem',
        sm: '2rem',
        lg: '4rem',
        xl: '5rem',
        '2xl': '6rem',
      },
    },
    colors: ({ colors }) => ({
      inherit: colors.inherit,
      current: colors.current,
      transparent: colors.transparent,
      black: colors.green[600],
      white: colors.white,
      whitish: "#f9f9f9",
      gray: colors.slate, // palette from 100 to 900
      darkpurple: "#4a00a0", // eg on mint with card button
      darkblue: "#000094", // eg on mint with matic button
      primary: { 500: "#7B13F5" }, // purple, o button
      primarylight: "#b558ff", // hover state on primary
      pinkpop: "#FF33CE", // eg highlighted text
      pinkfade: "#F8F3FF", // eg on footer
      // midgray: '#979797', // eg on "Forum: Whatsapp"
      // darkgray: '#202020',
      // blackish: '#101010',
      info: { 200: "#abe2fb", 500: "#00a0f2" },
      success: { 200: "#ddfcbd", 500: "#36ca00" },
      warning: { 200: "#fff8c3", 500: "#f9a621" }, // yellowish background (light), foreground (dark)
      error: { 200: "#ffbaca", 500: "#fc004f" },

      // default colors that we don't use:

      slate: colors.slate,
      // gray: colors.gray,
      // zinc: colors.zinc,
      // neutral: colors.neutral,
      // stone: colors.stone,
      // red: colors.red,
      // orange: colors.orange,
      // amber: colors.amber,
      // yellow: colors.yellow,
      // lime: colors.lime,
      // green: colors.green,
      // emerald: colors.emerald,
      // teal: colors.teal,
      // cyan: colors.cyan,
      // sky: colors.sky,
      // blue: colors.blue,
      // indigo: colors.indigo,
      // violet: colors.violet,
      // purple: colors.purple,
      // fuchsia: colors.fuchsia,
      // pink: colors.pink,
      // rose: colors.rose,
    }),
  },
  variants: {},
  corePlugins:{
    // preflight: false,   // disable Tailwind's resetting of styles
  },
  plugins: [require("@tailwindcss/typography"), require("daisyui")],
  daisyui: {
    themes: ["light"],
  },
}
