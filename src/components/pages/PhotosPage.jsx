import React from 'react'
import '../../App.css'
import './PhotosPage.css'
import PhotoCard from '../PhotoCard'

function PhotosPage() {
    return (
        <>
            <h1>Photos</h1>
            <div className="photo-card-container">
                <PhotoCard
                    photopaths={["/photos/portfolio/South Korea/DSC09123.jpg",
                        "/photos/portfolio/South Korea/DSC00021.jpg",
                        "/photos/portfolio/South Korea/DSC00085.jpg",]}
                    title="South Korea"
                    path='/southkorea'
                />
                <PhotoCard
                    photopaths={["/photos/portfolio/South Africa/DSC02715.jpg"]}
                    title="South Africa"
                    path='/services'
                />
                <PhotoCard
                    photopaths={["/photos/portfolio/Tanzania/DSC05649.jpg"]}
                    title="Tanzania"
                    path='/services'
                />
            </div>
        </>
    )
}

export default PhotosPage