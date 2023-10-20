import React from 'react'
import '../../App.css'
import PhotoGrid from '../PhotoGrid'
import Photo from '../Photo'

function SouthAfrica() {
    return (
        <>
            <h1>Photos / South Africa</h1>
            <Photo src='/portfolio/SouthKorea/DSC00021.jpg' />
            {/* <PhotoGrid photoSources={aws_sources} /> */}
        </>
    );
}

export default SouthAfrica;
