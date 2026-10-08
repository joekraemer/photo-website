import React from 'react';
import { Link } from 'react-router';

function NavMenuMobile({ menuItems, click, closeMobileMenu }) {
    // The closed menu stays in the DOM (it slides in), so keep its links out of
    // the tab order and away from screen readers until it opens.
    return (
        <ol
            id="nav-menu-mobile"
            className={click ? 'nav-menu-mobile active' : 'nav-menu-mobile'}
            aria-hidden={!click}
        >
            {menuItems.map((item, index) => (
                <li className='nav-item-mobile' key={index}>
                    <Link
                        to={item.link}
                        className='nav-links-mobile'
                        onClick={closeMobileMenu}
                        tabIndex={click ? undefined : -1}
                    >
                        {item.text}
                    </Link>
                </li>
            ))}
        </ol>
    );
}

export default NavMenuMobile;
