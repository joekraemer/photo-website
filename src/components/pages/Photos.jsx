import React from 'react'
import '../../App.css'
import './Photos.css'
import PhotoCard from '../PhotoCard'

function Photos() {
    return (
        <>
            <h1>Photos</h1>
            <div className="photo-card-container">
                <PhotoCard
                    src="/photos/portfolio/South Korea/DSC09123.jpg"
                    title="South Korea"
                    path='/services'
                />
                <PhotoCard
                    src="/photos/portfolio/South Africa/DSC02715.jpg"
                    title="South Africa"
                    path='/services'
                />
                <PhotoCard
                    src="/photos/portfolio/Tanzania/DSC05649.jpg"
                    title="Tanzania"
                    path='/services'
                />
            </div>
        </>
    )
}

export default Photos