import { describe, expect, it } from 'vitest';
import { createPrefetcher } from './prefetch';

function fakeImages() {
    const made = [];
    return { made, make: () => { const img = {}; made.push(img); return img; } };
}

describe('createPrefetcher', () => {
    it('requests each URL once', () => {
        const { made, make } = fakeImages();
        const prefetch = createPrefetcher(make);
        expect(prefetch('a.jpg')).toBe(true);
        expect(prefetch('a.jpg')).toBe(false);
        expect(prefetch('b.jpg')).toBe(true);
        expect(made.map((i) => i.src)).toEqual(['a.jpg', 'b.jpg']);
    });

    it('ignores missing or empty URLs', () => {
        const { made, make } = fakeImages();
        const prefetch = createPrefetcher(make);
        expect(prefetch(undefined)).toBe(false);
        expect(prefetch('')).toBe(false);
        expect(made).toHaveLength(0);
    });

    it('stays done after a load, but allows a retry after an error', () => {
        const { made, make } = fakeImages();
        const prefetch = createPrefetcher(make);
        prefetch('ok.jpg');
        made[0].onload();
        expect(prefetch('ok.jpg')).toBe(false);
        prefetch('bad.jpg');
        made[1].onerror();
        expect(prefetch('bad.jpg')).toBe(true);
    });
});
