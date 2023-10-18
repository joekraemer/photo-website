import React from 'react'
import '../../App.css'
import PhotoCard from '../PhotoCard'
import HeroSection from '../HeroSection'
import TextHeaderWithLine from '../TextHeaderWithLine'
import PhotoContainer from '../PhotoContiner'

function Home() {
    return (
        <>
            <HeroSection />
            <TextHeaderWithLine title='Recent Favorites' />
            <PhotoContainer photoSources={[
                "/photos/recentfavorites/DSC00266.jpg",
                "/photos/recentfavorites/DSC09335.jpg",
                "/photos/recentfavorites/DSC07277.jpg"]} />
            <PhotoContainer photoSources={[
                "/photos/recentfavorites/DSC05344.jpg",
                "/photos/recentfavorites/DSC05649.jpg"]} />


        </>
    )
}

export default Home