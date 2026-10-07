import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

// Start each new page at the top instead of keeping the previous scroll position.
function ScrollToTop() {
    const { pathname } = useLocation();
    useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
    return null;
}

export default ScrollToTop;
