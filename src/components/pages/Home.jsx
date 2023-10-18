import React from 'react'
import '../../App.css'
import PhotoCard from '../PhotoCard'
import HeroSection from '../HeroSection'
import TextHeaderWithLine from '../TextHeaderWithLine'
import PhotoGrid from '../PhotoGrid'

function Home() {
    return (
        <>
            <HeroSection />
            <TextHeaderWithLine title='Recent Favorites' />
            <PhotoGrid photoSources={[
                "/photos/recentfavorites/DSC00266.jpg",
                "/photos/recentfavorites/DSC09335.jpg",
                "/photos/recentfavorites/DSC07277.jpg",
                "/photos/recentfavorites/DSC05344.jpg",
                "/photos/recentfavorites/DSC05649.jpg"]} />


        </>
    )
}

export default Home