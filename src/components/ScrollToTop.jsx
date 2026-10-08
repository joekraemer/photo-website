import { useEffect } from 'react';
import { useLocation, useNavigationType } from 'react-router-dom';
import { pageKey } from '../services/lightboxNav';

// Start each new page at the top instead of keeping the previous scroll position.
// Back/Forward (POP) is left alone so the browser can restore where you were.
function ScrollToTop() {
    const page = pageKey(useLocation().pathname);
    const navigationType = useNavigationType();
    // Keyed on the page, so opening, stepping or closing a photo's lightbox
    // (which changes the URL) doesn't scroll the album behind it.
    useEffect(() => {
        if (navigationType !== 'POP') window.scrollTo(0, 0);
    }, [page]); // eslint-disable-line react-hooks/exhaustive-deps
    return null;
}

export default ScrollToTop;
