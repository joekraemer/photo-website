import React from 'react'
import './HeroSection.css'

function HeroSection() {
    return (
        <div className='hero__section__container'>
            <figure className="hero__section__figure">
                <img
                    src={`${import.meta.env.BASE_URL}photos/herophoto.webp`}
                    alt="Joe Kraemer standing on a sand dune"
                    className="hero__section__img"
                    width="936"
                    height="1111"
                    fetchpriority="high"
                />
            </figure>
            <p className="hero__section__text">
                My name is <span className="bold-name">Joe Kraemer</span><br /><br />
                I love traveling the world and sharing moments
            </p>
        </div>
    )
}

export default HeroSection
