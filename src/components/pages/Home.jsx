import React from 'react'
import '../../App.css'
import PhotoCard from '../PhotoCard'
import HeroSection from '../HeroSection'
import TextHeaderWithLine from '../TextHeaderWithLine'

function Home() {
    return (
        <>
            <HeroSection />
            <TextHeaderWithLine title='Recent Favorites' />
        </>
    )
}

export default Home