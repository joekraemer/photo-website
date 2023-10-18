import React from 'react'
import './PhotoContainer.css'
import Photo from './Photo'

function PhotoContainer({ photoSources }) {
    return (
        <div className="photo-container">
            {photoSources.map((src, index) => (
                <Photo key={index} src={src} />
            ))}
        </div>
    )
}

export default PhotoContainer