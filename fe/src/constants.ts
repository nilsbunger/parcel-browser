// the environment var here is read in dev and in build phase -- it's resolved before prod.
export const BACKEND_DOMAIN = process.env.REACT_APP_BACKEND_DOMAIN

console.assert(BACKEND_DOMAIN, "REACT_APP_BACKEND_DOMAIN is not set")
