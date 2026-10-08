import React, { useState, useEffect } from 'react';
import { Link } from 'react-router';
import './Navbar.css';
import NavMenuDesktop from './NavMenuDesktop';
import NavMenuMobile from './NavMenuMobile.jsx';

// Matches the 730px breakpoint in Navbar.css.
const isMobileWidth = () => window.innerWidth <= 730;

// Define the menu items
const menuItems = [
    { text: 'Photos', link: '/photos' },
    { text: 'Videos', link: '/videos' },
    { text: 'Contact', link: '/contact' },
];

function Navbar() {
    const [click, setClick] = useState(false);
    // Read the width on first render too, not only on resize, so the phone menu
    // works on a page that was loaded at phone width.
    const [mobileScreen, setMobileScreen] = useState(isMobileWidth);

    const handleClick = () => setClick(!click);
    const closeMobileMenu = () => setClick(false);

    useEffect(() => {
        const handleResize = () => {
            const mobile = isMobileWidth();
            setMobileScreen(mobile);
            if (!mobile) setClick(false);
        };
        handleResize();
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    // Escape closes the open phone menu.
    useEffect(() => {
        if (!click) return undefined;
        const onKey = (event) => { if (event.key === 'Escape') setClick(false); };
        document.addEventListener('keydown', onKey);
        return () => document.removeEventListener('keydown', onKey);
    }, [click]);

    return (
        <>
            <nav className='navbar'>
                <div className='navbar-container'>
                    <Link to="/" className="navbar-logo" onClick={closeMobileMenu}>
                        JAK Creative
                    </Link>
                    <button
                        type="button"
                        className='menu-icon'
                        onClick={handleClick}
                        aria-label={click ? 'Close menu' : 'Open menu'}
                        aria-expanded={click}
                        aria-controls="nav-menu-mobile"
                    >
                        <i className={click ? 'fas fa-times' : 'fas fa-bars'} aria-hidden="true" />
                    </button>

                    {/* Desktop Menu */}
                    {!mobileScreen && <NavMenuDesktop menuItems={menuItems} closeMobileMenu={closeMobileMenu} />}

                    {/* Mobile Menu */}
                    {mobileScreen && <NavMenuMobile menuItems={menuItems} click={click} closeMobileMenu={closeMobileMenu} />}
                </div>
            </nav>
        </>
    );
}

export default Navbar;
