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
