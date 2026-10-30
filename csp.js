import { createHash } from 'node:crypto';

// Content-Security-Policy for the built site, written into index.html as a
// <meta> tag because GitHub Pages cannot send response headers (issue #55).
// A meta CSP ignores frame-ancestors, report-uri and sandbox, so none are set.
//
// Every origin here is something index.html or the app actually loads:
//   - Font Awesome kit: script from kit.fontawesome.com, which fetches its
//     stylesheets from ka-f.fontawesome.com (connect-src), injects them as
//     inline <style> blocks (hence style-src 'unsafe-inline') and loads the
//     webfonts from ka-f.fontawesome.com
//   - Google Fonts (Montserrat): CSS from fonts.googleapis.com, files from
//     fonts.gstatic.com
//   - photos.json and the photos: the bucket in VITE_PHOTOS_BASE_URL
//   - data: images: the ThumbHash blur placeholders
// The inline GitHub Pages SPA path-restore script is allowed by its hash,
// computed from the final HTML so editing it cannot silently break it.

const FONT_AWESOME_KIT = 'https://kit.fontawesome.com';
const FONT_AWESOME_ASSETS = 'https://ka-f.fontawesome.com';
const GOOGLE_FONTS_CSS = 'https://fonts.googleapis.com';
const GOOGLE_FONTS_FILES = 'https://fonts.gstatic.com';

// The origin of an absolute http(s) URL, or null for a relative or bad value
// (the local-photos default is same-origin and needs no extra source).
export function photosOrigin(baseUrl) {
    if (!baseUrl) return null;
    try {
        const url = new URL(baseUrl);
        return url.protocol === 'https:' || url.protocol === 'http:' ? url.origin : null;
    } catch {
        return null;
    }
}

// 'sha256-...' sources for every inline <script> (one without a src attribute).
export function inlineScriptHashes(html) {
    const hashes = [];
    for (const match of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
        if (/\bsrc\s*=/i.test(match[1])) continue;
        const digest = createHash('sha256').update(match[2], 'utf8').digest('base64');
        hashes.push(`'sha256-${digest}'`);
    }
    return hashes;
}

export function buildCsp({ photos, scriptHashes = [] }) {
    const photoSrc = photos ? [photos] : [];
    const directives = {
        'default-src': ["'self'"],
        'script-src': ["'self'", FONT_AWESOME_KIT, ...scriptHashes],
        // 'unsafe-inline': the Font Awesome kit inserts its CSS as <style> blocks.
        'style-src': ["'self'", "'unsafe-inline'", GOOGLE_FONTS_CSS, FONT_AWESOME_ASSETS],
        'font-src': ["'self'", GOOGLE_FONTS_FILES, FONT_AWESOME_ASSETS],
        'img-src': ["'self'", 'data:', ...photoSrc],
        'connect-src': ["'self'", FONT_AWESOME_ASSETS, ...photoSrc],
        'object-src': ["'none'"],
        'base-uri': ["'self'"],
        'form-action': ["'none'"],
    };
    return Object.entries(directives)
        .map(([name, sources]) => `${name} ${sources.join(' ')}`)
        .join('; ');
}

// Puts the meta tag right after <meta charset> (which must stay first) so it
// precedes every script and stylesheet. The CSP holds no '"', '<' or '&'.
export function injectCspMeta(html, csp) {
    const tag = `<meta http-equiv="Content-Security-Policy" content="${csp}" />`;
    const charset = /<meta\s+charset=[^>]*>/i;
    if (!charset.test(html)) throw new Error('index.html has no <meta charset>; cannot place the CSP');
    return html.replace(charset, (m) => `${m}\n  ${tag}`);
}

// Vite plugin: adds the CSP meta tag near the top of <head> in the
// production build. Not applied to the dev server, whose HMR client and
// React Refresh preamble are inline scripts the policy would block.
export function cspPlugin() {
    let photos = null;
    return {
        name: 'content-security-policy',
        apply: 'build',
        configResolved(config) {
            photos = photosOrigin(config.env.VITE_PHOTOS_BASE_URL);
        },
        transformIndexHtml: {
            order: 'post',
            handler(html) {
                const csp = buildCsp({ photos, scriptHashes: inlineScriptHashes(html) });
                return injectCspMeta(html, csp);
            },
        },
    };
}
