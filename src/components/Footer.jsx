import React from 'react'
import { Link } from 'react-router-dom'
import './Footer.css'

function Footer() {
    return (
        <>
            <div className='footer'>
                <div className="footer-gray-line" />
                <div className='footer-container'>
                    <div className="footer-item">
                        <p>Email: jkraemer9@gmail.com</p>
                    </div>
                    <div className="footer-item">
                        <Link to="https://www.instagram.com/jak_creative_/" className="ig__link">
                            <i className='fa fa-instagram' id='instagram-logo' />   @jak_creative_
                        </Link>
                    </div>
                </div>
            </div>
        </>
    )
}

export default Footer