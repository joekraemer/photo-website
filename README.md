# Photography Website

A simple photography portfolio I built to learn JavaScript and React. Photos are
rendered by [`photo-sync/`](photo-sync/) into web sizes plus a `photos.json`
manifest, stored on Backblaze B2. The site reads
`photos.json` at runtime.

**Live site:** https://joekraemer.github.io/photo-website/

## Tech stack

- React 18 + React Router 7 (client-side routing)
- `photo-sync` (Python) + Backblaze B2 for photo hosting
- [Vite](https://vite.dev/) build tooling, [Vitest](https://vitest.dev/) for tests (Node 22)

## Adding photos

Whatever is in a shoot's `_web/` folder is on the site. The archive is laid
out as `<YEAR>/MM-DD-YYYY <Name>/`. Lightroom exports the photos rated 3 stars or
more into that shoot's `_web/` subfolder. `photo-sync` then renders three
sizes (the large one watermarked), reads the camera settings and uploads
everything with a new `photos.json`. An optional `album.md` in the shoot folder
sets the title, cover, intro or `hidden: true`. The full design is in
[issue #21](https://github.com/joekraemer/photo-website/issues/21), and the
Lightroom setup is in [docs/lightroom.md](docs/lightroom.md).

What `photo-sync` does with each shoot:

- **Files.** Every file in `_web/` that Pillow can read is published (JPEG,
  PNG, TIFF, WebP...). A file it can't read is a warning (for example a stray
  `.txt` or a `.heic`); a damaged file with an image extension is an error.
  Large panoramas are fine: JPEGs up to 1 gigapixel are decoded at reduced
  scale, other formats up to Pillow's ~179 MP limit.
- **Half-written exports.** A file changed in the last 60 seconds
  (`PHOTO_SETTLE_SECONDS`) is skipped, and `photos.json` waits for the next
  run so nothing disappears from the site mid-export.
- **Capture time** comes from EXIF `DateTimeOriginal`, with
  `OffsetTimeOriginal` when the camera recorded it (`taken_at` then carries the
  offset, e.g. `2024-06-15T09:00:00+03:00`). The export time is never used.
- **Cover.** `cover:` in `album.md` wins; the name match ignores case and
  accent encoding. Otherwise the highest-rated portrait photo (Lightroom star
  rating, read from the export's XMP), then the highest-rated landscape one;
  ties go to the earliest capture, unrated counts as 0.
- **Camera name.** Each photo's `exif` keeps the raw model in `camera` (e.g.
  `ILCE-6400`) and adds `body_name` (e.g. `Sony α6400`).
- **Watermark** is drawn with the bundled TeX Gyre Heros font
  (`photo-sync/photo_sync/fonts/`), so it looks the same on a Mac and in the
  container. It is white at `WATERMARK_OPACITY` (default 0.55) over a soft
  dark shadow, and `WATERMARK_SIZE` (default 0.07) of the photo's short side
  tall. Changing either re-renders every large image on the next sync.
- **album.md mistakes.** A wrong value or unknown key in `album.md` is a
  warning and that field is ignored. Only an `album.md` that can't be read at
  all (broken YAML) is an error, and that album stays off the site until fixed.

## Photos

The build reads `VITE_PHOTOS_BASE_URL`: the URL of the folder holding
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
is set up to run it once a day
([fleet PR #2](https://github.com/joekraemer/fleet/pull/2)) through `photo-sync/loop.py`, with the archive drive mounted
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
  `photos.json`, so the failed photos don't vanish from the site. Warnings
  (an `album.md` typo, an unreadable non-image file) don't hold it back.
- **One sync at a time.** A run takes an exclusive lock
  (`$TMPDIR/photo-sync.lock`, or `PHOTO_LOCK_FILE`). A second run while one is
  going prints that it is already in progress and exits 0 without changes.
  `--check` doesn't take the lock.

Settings: `PHOTO_SOURCE_ROOT`; `PHOTO_REQUIRE_SENTINEL` (on in the fleet
entry point, off for the plain CLI); `PHOTO_ALLOW_SHRINK`;
`PHOTO_SETTLE_SECONDS` (default 60); `PHOTO_LOCK_FILE`;
`PHOTO_REQUIRE_MOUNT` / `PHOTO_MOUNT_POINT` for a mount-point check, which
the fleet turns off: under Colima the USB drive is not a separate mount inside
the container, so the check cannot tell plugged from unplugged.

Dependencies for the image are pinned in `photo-sync/uv.lock`; `uv sync` in
`photo-sync/` gives the same environment locally.

## Available scripts

### `npm start`

Runs the Vite dev server at [http://localhost:5173/photo-website/](http://localhost:5173/photo-website/).
The page updates as you edit.

### `npm run build`

Builds the app for production into the `build/` folder. `npm run preview` serves
that build locally.

### `npm test`

Runs the unit tests once with Vitest.

## Deployment

The site deploys automatically to **GitHub Pages** via GitHub Actions
(`.github/workflows/deploy.yml`) on every push to `main`.

Because this is a React Router single-page app served from a project subpath
(`/photo-website/`), two pieces make deep links work:

- `base` in `vite.config.js` and `basename` (from `import.meta.env.BASE_URL`) on
  the `<Router>` set the correct base path.
- `public/404.html` + the decode script in `index.html` implement the
  [spa-github-pages](https://github.com/rafgraph/spa-github-pages) redirect so a
  refresh on `/photo-website/photos` resolves instead of 404ing.

### One-time repo setup

In the repo **Settings → Pages**, set **Source** to **GitHub Actions**. After
that, every push to `main` publishes automatically.
