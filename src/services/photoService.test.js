import { normalizeManifest } from './photoService';

const goodPhoto = (id) => ({
    id,
    alt: id,
    width: 100,
    height: 150,
    aspect: 0.67,
    sizes: { thumb: `p/${id}-thumb.webp`, medium: `p/${id}-medium.webp`, large: `p/${id}-large.webp` },
});

describe('normalizeManifest', () => {
    let warn;
    beforeEach(() => { warn = jest.spyOn(console, 'warn').mockImplementation(() => {}); });
    afterEach(() => warn.mockRestore());

    it('resolves photo keys against base_url', () => {
        const out = normalizeManifest({
            base_url: 'https://cdn.example/',
            albums: [{ slug: 'a', title: 'A', cover: 'p2', photos: [goodPhoto('p1'), goodPhoto('p2')] }],
        });
        expect(out.albums[0].photos[0].urls.thumb).toBe('https://cdn.example/p/p1-thumb.webp');
        expect(out.albums[0].coverPhoto.id).toBe('p2');
        expect(warn).not.toHaveBeenCalled();
    });

    it('skips malformed photos and albums instead of failing', () => {
        const out = normalizeManifest({
            base_url: 'https://cdn.example',
            albums: [
                { slug: 'ok', title: 'OK', photos: [goodPhoto('p1'), { id: 'broken' }, null] },
                { title: 'no slug', photos: [goodPhoto('p3')] },
                null,
                { slug: 'no-photos', title: 'Empty', photos: 'nope' },
            ],
        });
        expect(out.albums.map((a) => a.slug)).toEqual(['ok', 'no-photos']);
        expect(out.albums[0].photos.map((p) => p.id)).toEqual(['p1']);
        expect(out.albums[1].photos).toEqual([]);
        expect(out.albums[1].coverPhoto).toBeNull();
        expect(warn).toHaveBeenCalledTimes(4);
    });

    it('treats a manifest without an albums list as empty', () => {
        expect(normalizeManifest({}).albums).toEqual([]);
        expect(normalizeManifest(null).albums).toEqual([]);
    });
});
