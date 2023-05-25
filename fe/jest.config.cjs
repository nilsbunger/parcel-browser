/** @type {import('ts-jest').JestConfigWithTsJest} */

// set env vars before importing our elements which rely on them. We should make this more robust by taking them as
// arguments to the test function.
process.env.REACT_APP_BACKEND_DOMAIN = "http://test:5555"

module.exports = {
  preset: "ts-jest",
  // change environment to jsdom for react-testing-library.
  //   see https://testing-library.com/docs/react-testing-library/setup/

  testEnvironment: "jsdom",
  // testEnvironment: 'node',
}
