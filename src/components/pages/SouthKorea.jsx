import React from 'react'
import '../../App.css'
import PhotoGrid from '../PhotoGrid'

function SouthKorea() {
    return (
        <>
            <h1>Photos / South Korea</h1>
            <PhotoGrid photoSources={[
                "/photos/recentfavorites/DSC00266.jpg",
                "/photos/portfolio/South Korea/DSC00021.jpg",
                "/photos/portfolio/South Korea/DSC00085.jpg",
                "/photos/portfolio/South Korea/DSC00102-gen-filled.jpg",
                "/photos/portfolio/South Korea/DSC00105.jpg",
                "/photos/portfolio/South Korea/DSC00122.jpg",
                "/photos/portfolio/South Korea/DSC00159.jpg",
                "/photos/portfolio/South Korea/DSC09115-gen-filled.jpg",
                "/photos/portfolio/South Korea/DSC09123.jpg",
                "/photos/portfolio/South Korea/DSC09125.jpg",
                "/photos/portfolio/South Korea/DSC09133.jpg",
                "/photos/portfolio/South Korea/DSC09342.jpg",
                "/photos/portfolio/South Korea/DSC09358-gen-filled.jpg",
                "/photos/portfolio/South Korea/DSC09371.jpg",
                "/photos/portfolio/South Korea/DSC09409-gen-filled.jpg",
                "/photos/portfolio/South Korea/DSC09504-gen-filled-wide.jpg",
            ]} />
        </>
    )
}

export default SouthKorea