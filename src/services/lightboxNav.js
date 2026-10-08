// Grid layout and lightbox navigation helpers, kept free of React so they can
// be unit tested.

// Rows of three verticals or two horizontals, interleaved, using the manifest's
// aspect ratio instead of loading every image to measure it.
export function buildRows(photos) {
    const verticalRows = [];
    const horizontalRows = [];
    let vertical = [];
    let horizontal = [];

    photos.forEach((photo) => {
        if ((photo.aspect || 1) < 1) {
            vertical.push(photo);
            if (vertical.length === 3) { verticalRows.push(vertical); vertical = []; }
        } else {
            horizontal.push(photo);
            if (horizontal.length === 2) { horizontalRows.push(horizontal); horizontal = []; }
        }
    });
    if (vertical.length) verticalRows.push(vertical);
    if (horizontal.length) horizontalRows.push(horizontal);

    const rows = [];
    const maxLength = Math.max(verticalRows.length, horizontalRows.length);
    for (let i = 0; i < maxLength; i++) {
        if (verticalRows[i]) rows.push(verticalRows[i]);
        if (horizontalRows[i]) rows.push(horizontalRows[i]);
    }
    return rows;
}

// How many photos a full row of this kind holds: three verticals or two
// horizontals. A short last row still sizes its photos by this, so a lone
// leftover photo stays the size of the ones above it.
export function rowSlots(row) {
    return row.length && (row[0].aspect || 1) < 1 ? 3 : 2;
}

// A horizontal finger movement at least this long counts as a swipe.
export const SWIPE_MIN_PX = 50;

// -1 = previous photo (finger moved right), 1 = next (moved left), 0 = not a
// swipe: too short, or more vertical than horizontal (a scroll).
export function swipeDirection(dx, dy) {
    if (Math.abs(dx) < SWIPE_MIN_PX || Math.abs(dx) <= Math.abs(dy)) return 0;
    return dx < 0 ? 1 : -1;
}

// The index `step` away from `index`, or null past either end (no wrap-around).
export function stepIndex(index, step, length) {
    const next = index + step;
    return next >= 0 && next < length ? next : null;
}

// The page a URL belongs to for scroll purposes: /photos/<album>/<photo-id> is
// the album page with its lightbox open, so opening a photo isn't a new page.
export function pageKey(pathname) {
    const match = /^(\/photos\/[^/]+)\/[^/]+\/?$/.exec(pathname);
    return match ? match[1] : pathname;
}
