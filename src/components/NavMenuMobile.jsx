import React from 'react';
import { Link } from 'react-router-dom';

function NavMenuMobile({ menuItems, click, closeMobileMenu }) {
    return (
        <ol className={click ? 'nav-menu-mobile active' : 'nav-menu-mobile'}>
            {menuItems.map((item, index) => (
                <li className='nav-item-mobile' key={index}>
                    <Link to={item.link} className='nav-links-mobile' onClick={closeMobileMenu}>
                        {item.text}
                    </Link>
                </li>
            ))}
        </ol>
    );
}

export default NavMenuMobile;
