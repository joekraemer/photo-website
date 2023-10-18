import React from 'react'
import '../../App.css'
import PhotoGrid from '../PhotoGrid'

function SouthKorea() {
    return (
        <>
            <h1>Photos / South Korea</h1>
            <PhotoGrid photoSources={[
                "/photos/recentfavorites/DSC00266.jpg",
                "/photos/portfolio/SouthKorea/DSC00021.jpg",
                "/photos/portfolio/SouthKorea/DSC00085.jpg",
                "/photos/portfolio/SouthKorea/DSC00102-gen-filled.jpg",
                "/photos/portfolio/SouthKorea/DSC00105.jpg",
                "/photos/portfolio/SouthKorea/DSC00122.jpg",
                "/photos/portfolio/SouthKorea/DSC00159.jpg",
                "/photos/portfolio/SouthKorea/DSC09115-gen-filled.jpg",
                "/photos/portfolio/SouthKorea/DSC09123.jpg",
                "/photos/portfolio/SouthKorea/DSC09125.jpg",
                "/photos/portfolio/SouthKorea/DSC09133.jpg",
                "/photos/portfolio/SouthKorea/DSC09342.jpg",
                "/photos/portfolio/SouthKorea/DSC09358-gen-filled.jpg",
                "/photos/portfolio/SouthKorea/DSC09371.jpg",
                "/photos/portfolio/SouthKorea/DSC09409-gen-filled.jpg",
                "/photos/portfolio/SouthKorea/DSC09504-gen-filled-wide.jpg",
            ]} />
        </>
    )
}

export default SouthKorea