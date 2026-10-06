# Photography Website

A simple photography portfolio I built to learn JavaScript and React. Photos are
rendered by [`photo-sync/`](photo-sync/) into web sizes plus a `photos.json`
manifest, stored on Backblaze B2 and served through Cloudflare. The site reads
`photos.json` at runtime.

**Live site:** https://joekraemer.github.io/photo-website/

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Tech stack

- React 18 + React Router 6 (client-side routing)
- `photo-sync` (Python) + Backblaze B2 / Cloudflare for photo hosting
- Create React App build tooling

## Photos

The build reads `REACT_APP_PHOTOS_BASE_URL`: the URL of the folder holding
`photos.json`. When unset, the app loads `public/local-photos/` (gitignored),
which is where `photo-sync` writes with `TARGET=local`.

Local dev with sample photos:

```bash
cd photo-sync
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m photo_sync.sample_archive /tmp/sample-archive
.venv/bin/python -m photo_sync --source /tmp/sample-archive --target local --local-dir ../public/local-photos
cd .. && npm start
```

In CI the value comes from the repository variable `PHOTOS_BASE_URL`
(Settings -> Secrets and variables -> Actions -> Variables).

## Available scripts

### `npm start`

Runs the app in development mode at [http://localhost:3000](http://localhost:3000).
The page reloads on changes and lint errors show in the console.

### `npm run build`

Builds the app for production into the `build/` folder.

### `npm test`

Runs the test watcher.

## Deployment

The site deploys automatically to **GitHub Pages** via GitHub Actions
(`.github/workflows/deploy.yml`) on every push to `main`.

Because this is a React Router single-page app served from a project subpath
(`/photo-website/`), two pieces make deep links work:

- `homepage` in `package.json` and `basename={process.env.PUBLIC_URL}` on the
  `<Router>` set the correct base path.
- `public/404.html` + the decode script in `public/index.html` implement the
  [spa-github-pages](https://github.com/rafgraph/spa-github-pages) redirect so a
  refresh on `/photo-website/photos` resolves instead of 404ing.

### One-time repo setup

In the repo **Settings → Pages**, set **Source** to **GitHub Actions**. After
that, every push to `main` publishes automatically.
