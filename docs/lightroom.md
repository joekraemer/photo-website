# Lightroom Classic setup

The rule: **whatever is in a shoot's `_web/` folder is on the site.** Lightroom
puts files there; `photo-sync` does everything else (sizes, watermark, camera
settings, upload). These steps set Lightroom up once, then describe the routine.

The archive layout `photo-sync` expects:

```
<drive>/2023/06-10-2023 South Korea/DSC09123.ARW
<drive>/2023/06-10-2023 South Korea/_web/DSC09123.jpg   <- exported here
<drive>/2023/06-10-2023 South Korea/album.md            <- optional
```

Shoot folders are named `MM-DD-YYYY <Name>` inside a `YYYY` folder.
`photo-sync --check` lists any folder that doesn't follow this.

## One-time setup

### 1. Smart collection "Website"

1. Library module, **Collections** panel, click **+**, then **Create Smart Collection**.
2. Name: `Website`.
3. Match **all** of the following rules: **Rating** `is greater than or equal to` 3 stars.
4. Click **Create**.

This only gathers the candidates. Nothing reaches the site until you export.

### 2. Export preset "Website _web"

Select any photo, choose **File, Export**, and set:

| Section | Setting |
|---|---|
| Export To | **Same folder as original photo** |
| | Tick **Put in Subfolder**: `_web` |
| | Existing Files: **Overwrite WITHOUT WARNING** |
| File Naming | Untick **Rename To** (keeps the original file name) |
| File Settings | Format **JPEG**, Quality **92**, Color Space **sRGB** |
| Image Sizing | Untick **Resize to Fit** (full size; `photo-sync` makes the web sizes) |
| Output Sharpening | Optional: **Screen**, Standard |
| Metadata | Include: **All Except Camera Raw Info** |
| | Tick **Remove Location Info** (and **Remove Person Info**) |
| Watermarking | **Off** (`photo-sync` adds the watermark) |
| Post-Processing | **Do nothing** |

Then click **Add** at the bottom left, name the preset `Website _web`, and
cancel the export.

Why these matter:
- **Metadata** has to keep the camera settings and star rating. The site shows
  the camera, lens and exposure from it, and the album cover is picked by
  rating. Exports with metadata stripped show no settings on the site.
- **Location** must be left out. The site should never reveal where a photo
  was taken.
- **Same file name** means a re-export replaces the old copy instead of adding a
  duplicate.
- Only JPEG is supported. Other formats are skipped with a warning.

## Routine

**Add or update photos**

1. Rate the keepers 3 stars or more.
2. Open the **Website** collection and select the new or edited photos.
3. **File, Export with Preset, Website _web**.

The next sync picks them up (once a day on the fleet, or run it by hand).
Files changed less than a minute before a sync are left for the next one, in
case Lightroom is still writing them.

**Change an edit:** re-export the photo with the same preset. It overwrites the
old copy and the site updates on the next sync.

**Remove a photo from the site:** delete its file from the shoot's `_web/`
folder. Lowering the rating alone is not enough: it drops out of the smart
collection, but the exported file stays in `_web/` and stays on the site.

**Hide a whole shoot:** add `hidden: true` to its `album.md` (below).

## album.md (optional)

A text file in the shoot folder, next to `_web/`:

```markdown
---
title: Seoul in the Rain
cover: DSC09123.jpg
hidden: false
order: 1
sort: date
photos:
  - DSC09140.jpg
  - DSC09123.jpg
---
A short intro shown at the top of the album.
```

All fields are optional. Without `title`, the name comes from the folder.
Without `cover`, the cover is your highest-rated vertical photo, or the
highest-rated photo if the shoot has no verticals. `order` pins albums to the
front of the list (lowest first); the rest are newest first.

Photo order inside the album:
- `sort` is `date` (oldest first, the default), `date-desc` (newest first) or
  `name` (by file name). Photos with no capture date go last.
- `photos` lists file names to show first, in that order. Every other photo
  follows by `sort`. A listed name with no file in `_web/` is skipped with a
  warning.

The site lays photos out in rows of three verticals or two horizontals, so a
vertical and a horizontal next to each other in the list can land in
different rows. The lightbox steps through photos in the order they appear on
screen.

A typo in a field is reported as a warning and that field is ignored.

## Why not a Publish Service

Lightroom's Hard Drive publish service would track "Modified Photos to
Re-Publish", which is nice, but it writes every photo under one destination
folder (with one subfolder per collection). It can't write into each shoot's
own `_web/` folder, which is what keeps the masters and their web copies
together, so the export preset is the way to go.

## Checking an export

After exporting, run `photo-sync --check`. It reads the archive without changing
anything and lists naming problems, unreadable files and other warnings.
