# How we serve React and static files

We use Whitenoise, a popular Django package, to serve static files. Whitenoise
adds compression and caching headers. It works best with a CDN in front of it (we use cloudflare)
because then our django app only serves a particular version of a static file once.

Our static files come from React (under `frontend/`) and Django (under `<app>/static/`).

## Frontend static files and entrypoints

### Development

frontend/src is the source code for the React app. 
`yarn dev` puts assets into frontend/dist during development.

In package.json 'dev' script line, we specify the entrypoints, which are
files which won't have a hash appended to them.

Entrypoints are:
* 


### Production
