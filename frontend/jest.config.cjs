/** @type {import('ts-jest').JestConfigWithTsJest} */
module.exports = {
  preset: "ts-jest",
  // change environment to jsdom for react-testing-library.
  //   see https://testing-library.com/docs/react-testing-library/setup/

  testEnvironment: "jsdom",
  // testEnvironment: 'node',
}
