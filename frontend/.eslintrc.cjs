// Run lint with 'yarn eslint .'

module.exports = {
  root: true,
  parser: "@typescript-eslint/parser",
  parserOptions: {
    tsconfigRootDir: __dirname,
    project: ["./tsconfig.json"],
  },
  plugins: ["@typescript-eslint"],
  // See also configuration instructions in  https://typescript-eslint.io/docs/linting/configs
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:@typescript-eslint/recommended-requiring-type-checking",
    //"plugin:@typescript-eslint/strict",
    "prettier",
  ],
  rules: {
    "@typescript-eslint/restrict-template-expressions": "off",
    "@typescript-eslint/no-unnecessary-type-assertion": "off",
    "@typescript-eslint/no-misused-promises": "off",
    "@typescript-eslint/ban-ts-comment": "off",
    // Things we should turn on later but are too noisy right now:
    "@typescript-eslint/no-unsafe-assignment": "off",
    "@typescript-eslint/no-unsafe-member-access": "off",
    "@typescript-eslint/no-unsafe-call": "off",
    "@typescript-eslint/no-unsafe-return": "off",
    "@typescript-eslint/no-unsafe-argument": "off",
    "@typescript-eslint/no-explicit-any": "off",
    "@typescript-eslint/no-inferrable-types": "off",
  },
}
