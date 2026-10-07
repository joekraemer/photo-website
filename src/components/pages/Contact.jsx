import React from 'react'
import '../../App.css'
import './Contact.css'
import { EMAIL, INSTAGRAM_URL } from '../Footer'
import useDocumentTitle from '../../hooks/useDocumentTitle'

function Contact() {
    useDocumentTitle('Contact')
    return (
        <>
            <div className='contact__container'>
                <ol className='list'>
                    <p>Email: <a href={`mailto:${EMAIL}`} className="email__link">{EMAIL}</a></p>
                    <a href={INSTAGRAM_URL} className="ig__link" target="_blank" rel="noopener noreferrer">
                        <i className='fa fa-instagram' id='instagram-logo' aria-hidden="true" />   @jak_creative_
                    </a>
                </ol>
                <div className='text'>
                    <p>Contact me if you want to collaborate, purchase a high resolution print or just say "Hi"!</p>
                </div>
            </div>
        </>
    )
}

export default Contact
