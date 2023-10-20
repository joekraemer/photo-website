import React from 'react'
import { Link } from 'react-router-dom'
import '../../App.css'
import './Contact.css'
import Photo from '../Photo'

function Contact() {
    return (
        <>
            <div className='contact__container'>
                <ol className='list'>
                    <p>Email: jkraemer9@gmail.com</p>
                    <Link to="https://www.instagram.com/jak_creative_/" className="ig__link">
                        <i className='fa fa-instagram' id='instagram-logo' />   @jak_creative_
                    </Link>
                </ol>
                <div className='text'>
                    <p>Contact me if you want to collaborate, purchase a high resolution print or just say "Hi"!</p>
                </div>
            </div>

            <Photo src='/photos/portfolio/South Korea/DSC00021.jpg' />
        </>
    )
}

export default Contact