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

The bucket behind `PHOTOS_BASE_URL` needs a CORS rule that allows `GET` from
`https://joekraemer.github.io`, or the site cannot fetch `photos.json`. Setup
steps are in [issue #20](https://github.com/joekraemer/photo-website/issues/20).

### Scheduled sync on the fleet host

`photo-sync` also ships as a container image, `ghcr.io/joekraemer/photo-sync:main`,
built by `.github/workflows/photo-sync-image.yml` whenever `photo-sync/` changes
on `main`. The homelab fleet ([joekraemer/fleet](https://github.com/joekraemer/fleet))
runs it every 6 hours through `photo-sync/loop.py`, with the archive drive mounted
read-only. The site needs no rebuild after a sync: it fetches `photos.json` from
`PHOTOS_BASE_URL` at runtime (cached for at most 5 minutes).

Safety for unattended runs, because the drive is often unplugged:

- **Skip when the drive isn't there.** The container's entry point,
  `photo_sync.fleet`, skips the run (uploads and deletes nothing) when the
  archive folder is missing, has no `.photo-archive` sentinel file at its root,
  or holds no `<YEAR>/<shoot>/_web/` folders. The sentinel is checked again
  after the scan, so a drive pulled mid-run is caught too. Mark the real drive
  once with `touch /Volumes/<drive>/.photo-archive`.
- **Refuse to shrink the site.** Before writing `photos.json` and before
  pruning, `sync.run` compares against the published manifest. If a whole year
  disappears, or the album or photo count drops by more than 20%, it writes no
  manifest, prunes nothing, logs an `ERROR` and exits 1. Albums newly marked
  `hidden` in `album.md` don't count. For a deliberate cleanup, run once with
  `PHOTO_ALLOW_SHRINK=1`. The first real sync replaces the 3-album sample
  currently on B2; run it normally, since the real archive is almost certainly
  larger. Use the override only if that run logs the shrink `ERROR` and the
  ERROR shows just the sample albums going away.
- **Never compare blind.** If the published `photos.json` exists but can't be
  read or parsed, the run is held the same way (`ERROR`, exit 1). If there is
  no `photos.json` but photos are already on the target, the run publishes a
  new manifest but deletes nothing.
- **Keep the site on errors.** If any photo or `album.md` fails to read, the
  run still uploads the images it rendered but keeps the previous
  `photos.json`, so the failed photos don't vanish from the site.

Settings: `PHOTO_SOURCE_ROOT`; `PHOTO_REQUIRE_SENTINEL` (on in the fleet
entry point, off for the plain CLI); `PHOTO_ALLOW_SHRINK`;
`PHOTO_REQUIRE_MOUNT` / `PHOTO_MOUNT_POINT` for a mount-point check, which
the fleet turns off: under Colima the USB drive is not a separate mount inside
the container, so the check cannot tell plugged from unplugged.

Dependencies for the image are pinned in `photo-sync/uv.lock`; `uv sync` in
`photo-sync/` gives the same environment locally.

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
