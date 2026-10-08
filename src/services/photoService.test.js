import { exifLine, loadedImageSrc, normalizeManifest, placeholderProps } from './photoService';

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
    beforeEach(() => { warn = vi.spyOn(console, 'warn').mockImplementation(() => {}); });
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

describe('exifLine', () => {
    it('prefers the friendly body_name over the raw camera model', () => {
        expect(exifLine({ camera: 'ILCE-6400', body_name: 'Sony α6400', iso: 100 })).toBe('Sony α6400 · ISO 100');
    });

    it('falls back to the raw camera model', () => {
        expect(exifLine({ camera: 'ILCE-6400', aperture: 'f/4' })).toBe('ILCE-6400 · f/4');
    });
});

describe('placeholderProps', () => {
    it('paints a valid colour and clears it on load', () => {
        const props = placeholderProps({ color: '#3a5f7d' });
        expect(props.style).toEqual({ backgroundColor: '#3a5f7d' });
        const img = { style: { backgroundColor: '#3a5f7d' } };
        props.onLoad({ currentTarget: img });
        expect(img.style.backgroundColor).toBe('');
    });

    it('ignores a missing or malformed colour', () => {
        expect(placeholderProps({})).toEqual({});
        expect(placeholderProps({ color: 'red; background:url(x)' })).toEqual({});
        expect(placeholderProps(null)).toEqual({});
    });
});

describe('loadedImageSrc', () => {
    it('returns the URL the browser picked once the image has loaded', () => {
        expect(loadedImageSrc({ complete: true, naturalWidth: 500, currentSrc: 'm.jpg', src: 't.jpg' })).toBe('m.jpg');
    });

    it('falls back to src when currentSrc is empty', () => {
        expect(loadedImageSrc({ complete: true, naturalWidth: 500, currentSrc: '', src: 't.jpg' })).toBe('t.jpg');
    });

    it('returns null for images that are not loaded or are broken', () => {
        expect(loadedImageSrc(null)).toBeNull();
        expect(loadedImageSrc({ complete: false, naturalWidth: 0, currentSrc: 't.jpg' })).toBeNull();
        expect(loadedImageSrc({ complete: true, naturalWidth: 0, currentSrc: 't.jpg' })).toBeNull();
    });
});
