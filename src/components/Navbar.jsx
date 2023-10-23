import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './Navbar.css';
import NavMenuDesktop from './NavMenuDesktop';
import NavMenuMobile from './NavMenuMobile.jsx';

function Navbar() {
    const [click, setClick] = useState(false);
    const [mobileScreen, setMobileScreen] = useState(false);

    const handleClick = () => setClick(!click);
    const closeMobileMenu = () => setClick(false);

    // Define the menu items
    const menuItems = [
        { text: 'Photos', link: '/photos' },
        { text: 'Videos', link: '/videos' },
        { text: 'Contact', link: '/contact' },
    ];

    // Update the mobileScreen state when the window is resized
    useEffect(() => {
        const handleResize = () => {
            setMobileScreen(window.innerWidth < 768);
        };

        window.addEventListener('resize', handleResize);

        // Clean up the event listener when the component unmounts
        return () => {
            window.removeEventListener('resize', handleResize);
        };
    }, []);

    return (
        <>
            <nav className='navbar'>
                <div className='navbar-container'>
                    <Link to="/" className="navbar-logo">
                        JAK Creative
                    </Link>
                    <div className='menu-icon' onClick={handleClick}>
                        <i className={click ? 'fas fa-times' : 'fas fa-bars'} />
                    </div>

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
