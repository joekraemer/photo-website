import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '../components/Button.jsx';
import './Navbar.css'

function Navbar() {
    const [click, setClick] = useState(false);
    const [button, setButton] = useState(true);

    const handleClick = () => setClick(!click);
    const closeMobileMenu = () => setClick(false);

    const showButton = () => {
        if (window.innerWidth <= 960) {
            setButton(false)
        }
        else {
            setButton(true)
        }
    }

    useEffect(() => {
        showButton()
    }, [])

    window.addEventListener('resize', showButton);

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
                    <ol className='nav-menu-desktop'>
                        <li className='nav-item'>
                            <Link to='/photos' className='nav-links' onClick={closeMobileMenu}>
                                Photos
                            </Link>
                        </li>
                        <li className='nav-item'>
                            <Link to='/videos' className='nav-links' onClick={closeMobileMenu}>
                                Videos
                            </Link>
                        </li>
                        <li className='nav-item'>
                            <Link to='/contact' className='nav-links' onClick={closeMobileMenu}>
                                Contact
                            </Link>
                        </li>
                    </ol>

                    {/* TODO: This could be a different module */}
                    <ol className={click ? 'nav-menu-mobile active' : 'nav-menu-mobile'}>
                        <li className='nav-item-mobile'>
                            <Link to='/photos' className='nav-links-mobile' onClick={closeMobileMenu}>
                                Photos
                            </Link>
                        </li>
                        <li className='nav-item-mobile'>
                            <Link to='/videos' className='nav-links-mobile' onClick={closeMobileMenu}>
                                Videos
                            </Link>
                        </li>
                        <li className='nav-item-mobile'>
                            <Link to='/contact' className='nav-links-mobile' onClick={closeMobileMenu}>
                                Contact
                            </Link>
                        </li>
                    </ol>
                </div>
            </nav>
        </>
    )
}

export default Navbar