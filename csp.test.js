import { createHash } from 'node:crypto';
import { buildCsp, injectCspMeta, inlineScriptHashes, photosOrigin } from './csp.js';

const B2 = 'https://joekraemer-photos.s3.us-east-005.backblazeb2.com';

function directive(csp, name) {
    const found = csp.split('; ').find((d) => d.startsWith(`${name} `));
    return found ? found.slice(name.length + 1).split(' ') : null;
}

describe('photosOrigin', () => {
    it('reduces an absolute URL to its origin', () => {
        expect(photosOrigin(`${B2}/`)).toBe(B2);
        expect(photosOrigin(`${B2}/some/prefix`)).toBe(B2);
    });

    it('returns null for unset, relative or non-http values', () => {
        expect(photosOrigin(undefined)).toBeNull();
        expect(photosOrigin('')).toBeNull();
        expect(photosOrigin('/photo-website/local-photos')).toBeNull();
        expect(photosOrigin('javascript:alert(1)')).toBeNull();
    });
});

describe('inlineScriptHashes', () => {
    it('hashes inline scripts and skips external ones', () => {
        const body = "\n    console.log('hi')\n  ";
        const html = `<script src="https://kit.fontawesome.com/x.js"></script>
<script type="text/javascript">${body}</script>
<script type="module" crossorigin src="/photo-website/assets/index.js"></script>`;
        const expected = createHash('sha256').update(body).digest('base64');
        expect(inlineScriptHashes(html)).toEqual([`'sha256-${expected}'`]);
    });
});

describe('buildCsp', () => {
    it('allows the photo bucket for images and photos.json', () => {
        const csp = buildCsp({ photos: B2 });
        expect(directive(csp, 'img-src')).toEqual(["'self'", 'data:', B2]);
        expect(directive(csp, 'connect-src')).toContain(B2);
    });

    it('adds no photo origin when photos are same-origin', () => {
        const csp = buildCsp({ photos: null });
        expect(directive(csp, 'img-src')).toEqual(["'self'", 'data:']);
    });

    it('allows scripts only from self, the Font Awesome kit and given hashes', () => {
        const csp = buildCsp({ photos: B2, scriptHashes: ["'sha256-abc'"] });
        expect(directive(csp, 'script-src')).toEqual(["'self'", 'https://kit.fontawesome.com', "'sha256-abc'"]);
        expect(csp).not.toMatch(/unsafe-eval/);
        expect(directive(csp, 'object-src')).toEqual(["'none'"]);
        expect(directive(csp, 'base-uri')).toEqual(["'self'"]);
    });

    it('omits directives a meta CSP ignores', () => {
        expect(buildCsp({ photos: B2 })).not.toMatch(/frame-ancestors|report-uri|sandbox/);
    });
});

describe('injectCspMeta', () => {
    it('places the tag right after <meta charset>, before any script', () => {
        const html = '<head>\n  <meta charset="utf-8" />\n  <script src="a.js"></script>\n</head>';
        const out = injectCspMeta(html, "default-src 'self'");
        const meta = out.indexOf('http-equiv="Content-Security-Policy"');
        expect(meta).toBeGreaterThan(out.indexOf('charset'));
        expect(meta).toBeLessThan(out.indexOf('<script'));
    });

    it('fails the build when there is no <meta charset> to anchor on', () => {
        expect(() => injectCspMeta('<head></head>', "default-src 'self'")).toThrow(/charset/);
    });
});
