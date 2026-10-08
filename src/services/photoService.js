// Loads photos.json (written by photo-sync) and turns its relative keys into URLs.
//
// VITE_PHOTOS_BASE_URL is where photos.json lives (the public B2 bucket's
// S3-style URL). When unset, the app falls back to the local dev output in
// public/local-photos/.

import { thumbHashToDataURL } from 'thumbhash';

const DEFAULT_BASE = `${import.meta.env.BASE_URL}local-photos`;

export const PHOTOS_BASE_URL = (import.meta.env.VITE_PHOTOS_BASE_URL || DEFAULT_BASE).replace(/\/+$/, '');

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

const SIZE_KEYS = ['thumb', 'medium', 'large'];

const isText = (value) => typeof value === 'string' && value.length > 0;

// A photo the site can draw: an id and all three size keys.
function isValidPhoto(photo) {
    return Boolean(photo) && typeof photo === 'object' && isText(photo.id)
        && Boolean(photo.sizes) && SIZE_KEYS.every((key) => isText(photo.sizes[key]));
}

// One bad photo or album must not blank the whole site: skip it and warn.
export function normalizeManifest(manifest) {
    // Photo keys are relative. Resolve them against base_url when the manifest
    // names one, otherwise against the folder photos.json was loaded from.
    const source = manifest && typeof manifest === 'object' ? manifest : {};
    const base = (isText(source.base_url) ? source.base_url : PHOTOS_BASE_URL).replace(/\/+$/, '');
    const rawAlbums = Array.isArray(source.albums) ? source.albums : [];
    if (!Array.isArray(source.albums)) console.warn('photos.json: "albums" is not a list; showing no albums');

    const albums = [];
    rawAlbums.forEach((album, albumIndex) => {
        if (!album || typeof album !== 'object' || !isText(album.slug)) {
            console.warn(`photos.json: skipping album #${albumIndex}: missing slug`, album);
            return;
        }
        const rawPhotos = Array.isArray(album.photos) ? album.photos : [];
        const photos = [];
        rawPhotos.forEach((photo, photoIndex) => {
            if (!isValidPhoto(photo)) {
                console.warn(`photos.json: skipping photo #${photoIndex} in album "${album.slug}": missing id or sizes`, photo);
                return;
            }
            photos.push({
                ...photo,
                albumSlug: album.slug,
                urls: {
                    thumb: `${base}/${photo.sizes.thumb}`,
                    medium: `${base}/${photo.sizes.medium}`,
                    large: `${base}/${photo.sizes.large}`,
                },
            });
        });
        const cover = photos.find((p) => p.id === album.cover) || photos[0] || null;
        albums.push({
            ...album,
            title: isText(album.title) ? album.title : album.slug,
            date: isText(album.date) ? album.date : '',
            intro: isText(album.intro) ? album.intro : '',
            photos,
            coverPhoto: cover,
        });
    });
    return { ...source, albums };
}

const HEX_COLOR = /^#[0-9a-f]{6}$/i;
const THUMBHASH = /^[A-Za-z0-9+/]{6,64}={0,2}$/;
const blurCache = new Map();

// Decodes a ThumbHash (photo.thumbhash from photo-sync, ~23 bytes of base64)
// into a tiny blurred PNG data URL. Cached, since a photo's preview is
// needed again by the grid, the lightbox and the album cover.
export function blurDataUrl(hash) {
    if (!isText(hash) || !THUMBHASH.test(hash)) return null;
    if (!blurCache.has(hash)) {
        let url = null;
        try {
            url = thumbHashToDataURL(Uint8Array.from(atob(hash), (c) => c.charCodeAt(0)));
        } catch {
            url = null; // a corrupt hash just falls back to the colour
        }
        blurCache.set(hash, url);
    }
    return blurCache.get(hash);
}

// Props that paint a blurred preview (photo.thumbhash) over the photo's
// average colour (photo.color) while it loads, then clear both so they can't
// show around a letterboxed photo. Either one alone still works, and photos
// with neither get no props and load as before.
export function placeholderProps(photo) {
    const color = photo && isText(photo.color) && HEX_COLOR.test(photo.color) ? photo.color : null;
    const blur = photo ? blurDataUrl(photo.thumbhash) : null;
    if (!color && !blur) return {};
    const style = {};
    if (color) style.backgroundColor = color;
    if (blur) {
        style.backgroundImage = `url("${blur}")`;
        style.backgroundSize = 'cover';
        style.backgroundPosition = 'center';
    }
    return {
        style,
        onLoad: (event) => {
            const s = event.currentTarget.style;
            s.backgroundColor = '';
            s.backgroundImage = '';
        },
    };
}

export function exifLine(exif) {
    if (!exif) return '';
    return [
        // body_name is the friendly camera name (e.g. "Sony α6400") when
        // photo-sync knows it; otherwise the raw EXIF model (e.g. "ILCE-6400").
        exif.body_name || exif.camera,
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
    const date = new Date(y, m - 1, d);
    if (Number.isNaN(date.getTime())) return '';
    return date.toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });
}
