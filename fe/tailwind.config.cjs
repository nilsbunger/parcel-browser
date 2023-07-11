module.exports = {
    darkMode: "unusedDarkModeClass", // disable dark mode for now. Remove to fallback to listening to prefer-media-scheme
    // Include Django template dirs (../*/templates/) so Tailwind can see classes used in Django templates.
    content: ["./src/**/*.{html,js,ts,tsx}", "../be/**/templates/**/*.html"],
    theme: {
        extend: {
            opacity: ["disabled"],
        },
        fontFamily: {
            acc: ["turboserif", "serif"],
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
        // colors. By convention, low numbers like '100' are very light, while high numbers like '900' are very dark.
        colors: ({colors}) => ({
            inherit: colors.inherit,
            current: colors.current,
            transparent: colors.transparent,

            // *************************************
            // Turboprop colors May 2023:
            white: colors.white,
            acc: {   // accent color -- Yellows
                '800': '#332F1A',
                '600': '#6C6322',
                '400': '#9B921E',
                '300': '#C9BE13',
                DEFAULT: '#EADE00', // "TP Yellow"
                '100': '#FFF200'
            },
            prim: { // primary color
                DEFAULT: '#00142B', // "TP Blue"
                '850': '#082345',
                '800': '#133260',
                '600': '#3B5995',
                '400': '#778ECA',
                '200': '#C9D5FF',
            },
            gray: {
                '900': '#1e1e1e',
                '800': '#2e2e2d',
                '600': '#656563',
                '400': '#9E9E9D',
                DEFAULT: '#C9C9C7', // "TP Gray"
                '300': '#cEcDc9',
                '200': '#DEDDD8',
                'wheat': '#F3F1ED', // "TP Wheat"
            },
            // *************************************
            // form controls and messages:
            info: {200: "#abe2fb", 500: "#00a0f2"},
            success: {200: "#ddfcbd", 500: "#36ca00"},
            warning: {200: "#fff8c3", 500: "#f9a621"}, // yellowish background (light), foreground (dark)
            error: {200: "#ffbaca", 500: "#fc004f"},
            required: {200: "#ffbaca", 500: "#fc004f"},
        }),
    },
    variants: {},
    corePlugins: {
        preflight: false,   // disable Tailwind's resetting of styles, it interferes with mantine.
    },
    plugins: [require("@tailwindcss/typography"), require("daisyui")],
    daisyui: {
        styled: true,
        themes: [
            {
                "light": {
                    // From DaisyUI:
                    'color-scheme': 'light',
                    // primary: '#570df8',
                    // 'primary-content': '#ffffff',
                    // secondary: '#f000b8',
                    // 'secondary-content': '#ffffff',
                    // accent: '#37cdbe',
                    // 'accent-content': '#163835',
                    // neutral: '#3d4451',
                    // 'neutral-content': '#ffffff',
                    // 'base-100': '#ffffff',
                    // 'base-200': '#F2F2F2',
                    // 'base-300': '#E5E6E6',
                    // 'base-content': '#1f2937',


                    // primary: '#00152c',
                    // secondary: "#EADE00",
                    // accent: "#EADE00",
                    // neutral: "#C9C9C7",
                    // // "base-100": "var(--color-gray-wheat)",
                    //
                    // DaisyUI css variables (ref: https://daisyui.com/docs/themes/#-5):
                    "--rounded-btn": "0.25rem",
                    "--rounded-box": "1rem", // border radius rounded-box utility class, used in card and other large boxes
                    "--rounded-badge": "1.9rem", // border radius rounded-badge utility class, used in badges and similar
                    "--animation-btn": "0.25s", // duration of animation when you click on button
                    "--animation-input": "0.2s", // duration of animation for inputs like checkbox, toggle, radio, etc
                    "--btn-text-case": "none", // set default text transform for buttons
                    "--btn-focus-scale": "0.95", // scale transform of button when you focus on it
                    "--border-btn": "1px", // border width of buttons
                    "--tab-border": "1px", // border width of tabs
                    "--tab-radius": "0.5rem", // border radius of tabs

                }
            }],
    },
}

// *************************************
// Old color schemes:
// *************************************
// gray: colors.slate, // palette from 100 to 900
// darkpurple: "#4a00a0", // eg on mint with card button
// darkblue: "#000094", // eg on mint with matic button
// primary: {500: "#7B13F5"}, // purple, o button
// primarylight: "#b558ff", // hover state on primary
// pinkpop: "#FF33CE", // eg highlighted text
// pinkfade: "#F8F3FF", // eg on footer
// midgray: '#979797', // eg on "Forum: Whatsapp"
// darkgray: '#202020',
// blackish: '#101010',

// default colors that we don't use:

// slate: colors.slate,
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
