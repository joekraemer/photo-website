# Photography Website

A simple photography portfolio I built to learn JavaScript and React. Photos are
hosted on AWS S3 and served to the client through AWS Amplify (Cognito identity
pool for unauthenticated read access).

**Live site:** https://joekraemer.github.io/photo-website/

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Tech stack

- React 18 + React Router 6 (client-side routing)
- AWS Amplify Storage (S3) for photo hosting
- Create React App build tooling

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
