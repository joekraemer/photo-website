import React from 'react'
import '../../App.css'
import HeroSection from '../HeroSection'
import TextHeaderWithLine from '../TextHeaderWithLine'
import PhotoGrid from '../PhotoGrid'

function Home() {
    return (
        <>
            <HeroSection />
            <TextHeaderWithLine title='Recent Favorites' />
            <PhotoGrid photoSources={[
                "recentfavorites/DSC00266.jpg",
                "recentfavorites/DSC09335.jpg",
                "recentfavorites/DSC07277.jpg",
                "recentfavorites/DSC05344.jpg",
                "recentfavorites/DSC05649.jpg"]} />


        </>
    )
}

export default Home