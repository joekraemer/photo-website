// Starts downloading an image into the browser cache ahead of time, at most
// once per URL. Used for a grid photo's large size when the pointer rests on
// it (so a click opens it fast) and for the lightbox's neighbours.
export function createPrefetcher(makeImage) {
    const requested = new Map();
    return function prefetch(url) {
        if (typeof url !== 'string' || url === '' || requested.has(url)) return false;
        const img = makeImage();
        // Keep a reference until it settles so the request isn't dropped early.
        requested.set(url, img);
        const settle = () => { requested.set(url, true); };
        img.onload = settle;
        img.onerror = () => { requested.delete(url); };
        img.src = url;
        return true;
    };
}

export const prefetchImage = createPrefetcher(() => new Image());

// A pointer sweeping across the grid shouldn't fetch every photo it crosses,
// so hover waits this long before prefetching. Touch and focus fetch at once.
export const HOVER_INTENT_MS = 80;
