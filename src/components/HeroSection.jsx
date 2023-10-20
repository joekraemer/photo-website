import React from 'react'
import './HeroSection.css'

function HeroSection() {
    return (
        <div className='hero__section__container'>
            <figure className="hero__section__figure">
                <img src="/photos/herophoto.png" alt="Hero Photo" className="hero__section__img" />
            </figure>
            <p className="hero__section__text">
                My name is <span className="bold-name">Joe Kraemer</span><br /><br />
                I love traveling the world and sharing moments
            </p>
        </div>
    )
}

export default HeroSection