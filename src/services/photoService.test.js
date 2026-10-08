import { blurDataUrl, exifLine, normalizeManifest, placeholderProps } from './photoService';

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

    it('paints a ThumbHash blur over the colour and clears both on load', () => {
        const hash = '4hcODgZ3ePd4iMiIh3p4eWeHvHAAmGc='; // a real sample photo
        const props = placeholderProps({ color: '#3a5f7d', thumbhash: hash });
        expect(props.style.backgroundColor).toBe('#3a5f7d');
        expect(props.style.backgroundImage).toMatch(/^url\("data:image\/png;base64,/);
        expect(props.style.backgroundSize).toBe('cover');
        const img = { style: { ...props.style } };
        props.onLoad({ currentTarget: img });
        expect(img.style.backgroundColor).toBe('');
        expect(img.style.backgroundImage).toBe('');
    });

    it('uses the blur alone when there is no colour', () => {
        const props = placeholderProps({ thumbhash: '4hcODgZ3ePd4iMiIh3p4eWeHvHAAmGc=' });
        expect(props.style.backgroundColor).toBeUndefined();
        expect(props.style.backgroundImage).toMatch(/^url\("data:image\/png/);
    });

    it('ignores a malformed ThumbHash and keeps the colour', () => {
        expect(placeholderProps({ color: '#3a5f7d', thumbhash: 'x") ; evil' }).style)
            .toEqual({ backgroundColor: '#3a5f7d' });
        expect(blurDataUrl('not base64!')).toBeNull();
        expect(blurDataUrl(42)).toBeNull();
    });
});
