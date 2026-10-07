import React from 'react'
import './Footer.css'
import '../components/pages/Contact.css'

export const EMAIL = 'jkraemer9@gmail.com'
export const INSTAGRAM_URL = 'https://www.instagram.com/jak_creative_/'

function Footer() {
    return (
        <>
            <div className='footer'>
                <div className="footer-gray-line" />
                <div className='footer-container'>
                    <div className="footer-item">
                        <p>Email: <a href={`mailto:${EMAIL}`} className="email__link">{EMAIL}</a></p>
                    </div>
                    <div className="footer-item">
                        <a href={INSTAGRAM_URL} className="ig__link" target="_blank" rel="noopener noreferrer">
                            <i className='fa fa-instagram' id='instagram-logo' aria-hidden="true" />   @jak_creative_
                        </a>
                    </div>
                </div>
            </div>
        </>
    )
}

export default Footer
