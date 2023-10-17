import React from 'react'
import './PhotoContainer.css'

function PhotoContainer(props) {
    return (
        <div className="photo-container">
            <figure className='photo-container__figure'>
                <img src="/photos/recentfavorites/DSC05344.jpg" alt="" className="photo-container__img" />
            </figure>
            <figure className='photo-container__figure'>
                <img src="/photos/recentfavorites/DSC05649.jpg" alt="" className="photo-container__img" />
            </figure>
        </div>
    )
}

export default PhotoContainer