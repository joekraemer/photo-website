import React, { useState, useEffect } from 'react'
import '../../App.css'
import HeroSection from '../HeroSection'
import TextHeaderWithLine from '../TextHeaderWithLine'
import PhotoGrid from '../PhotoGrid'
import { listPhotosInFolder } from '../../services/AWSService';

function Home() {

    const [allPhotoData, setAllPhotoData] = useState([]);

    // Grab all of the fotos in recent favorites
    useEffect(() => {
        const fetchData = async () => {
            try {
                const photoObj = await listPhotosInFolder('recentfavorites');

                setAllPhotoData(photoObj);
            } catch (error) {
                console.error('Error fetching recent favorites:', error);
            }
        };

        fetchData();
    }, []);


    return (
        <>
            <HeroSection />
            <TextHeaderWithLine title='Recent Favorites' />
            <PhotoGrid photoSources={allPhotoData} />
        </>
    )
}

export default Home