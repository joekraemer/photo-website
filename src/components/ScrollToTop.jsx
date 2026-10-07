import { useEffect } from 'react';
import { useLocation, useNavigationType } from 'react-router-dom';

// Start each new page at the top instead of keeping the previous scroll position.
// Back/Forward (POP) is left alone so the browser can restore where you were.
function ScrollToTop() {
    const { pathname } = useLocation();
    const navigationType = useNavigationType();
    useEffect(() => {
        if (navigationType !== 'POP') window.scrollTo(0, 0);
    }, [pathname, navigationType]);
    return null;
}

export default ScrollToTop;
