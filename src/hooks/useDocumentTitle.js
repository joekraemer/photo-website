import { useEffect } from 'react';

export const SITE_TITLE = 'Joe Kraemer — Photography';

// Sets the browser tab title; pass nothing for the site-wide title.
export default function useDocumentTitle(title) {
    useEffect(() => {
        document.title = title ? `${title} — Joe Kraemer` : SITE_TITLE;
    }, [title]);
}
