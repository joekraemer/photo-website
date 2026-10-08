import React from 'react';
import { Link } from 'react-router';

function NavMenuDesktop({ menuItems, closeMobileMenu }) {
    return (
        <ol className='nav-menu-desktop'>
            {menuItems.map((item, index) => (
                <li className='nav-item' key={index}>
                    <Link to={item.link} className='nav-links' onClick={closeMobileMenu}>
                        {item.text}
                    </Link>
                </li>
            ))}
        </ol>
    );
}

export default NavMenuDesktop;
