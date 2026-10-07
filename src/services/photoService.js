// Loads photos.json (written by photo-sync) and turns its relative keys into URLs.
//
// REACT_APP_PHOTOS_BASE_URL is where photos.json lives, e.g. the Cloudflare
// hostname in front of the B2 bucket. When unset, the app falls back to the
// local dev output in public/local-photos/.

const DEFAULT_BASE = `${process.env.PUBLIC_URL || ''}/local-photos`;

export const PHOTOS_BASE_URL = (process.env.REACT_APP_PHOTOS_BASE_URL || DEFAULT_BASE).replace(/\/+$/, '');

let manifestPromise = null;

export function loadManifest() {
    if (!manifestPromise) {
        manifestPromise = fetch(`${PHOTOS_BASE_URL}/photos.json`, { cache: 'no-cache' })
            .then((res) => {
                if (!res.ok) throw new Error(`photos.json: HTTP ${res.status}`);
                return res.json();
            })
            .then(normalizeManifest)
            .catch((err) => {
                manifestPromise = null; // allow a retry on the next mount
                throw err;
            });
    }
    return manifestPromise;
}

function normalizeManifest(manifest) {
    // Photo keys are relative. Resolve them against base_url when the manifest
    // names one, otherwise against the folder photos.json was loaded from.
    const base = (manifest.base_url || PHOTOS_BASE_URL).replace(/\/+$/, '');
    const albums = (manifest.albums || []).map((album) => {
        const photos = (album.photos || []).map((photo) => ({
            ...photo,
            albumSlug: album.slug,
            urls: {
                thumb: `${base}/${photo.sizes.thumb}`,
                medium: `${base}/${photo.sizes.medium}`,
                large: `${base}/${photo.sizes.large}`,
            },
        }));
        const cover = photos.find((p) => p.id === album.cover) || photos[0] || null;
        return { ...album, photos, coverPhoto: cover };
    });
    return { ...manifest, albums };
}

export function exifLine(exif) {
    if (!exif) return '';
    return [
        exif.camera,
        exif.lens,
        exif.focal_length,
        exif.aperture,
        exif.shutter,
        exif.iso ? `ISO ${exif.iso}` : null,
    ].filter(Boolean).join(' · ');
}

export function formatAlbumDate(isoDate) {
    if (!isoDate) return '';
    const [y, m, d] = isoDate.split('-').map(Number);
    return new Date(y, m - 1, d).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });
}
