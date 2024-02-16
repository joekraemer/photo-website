import React, { useState, useEffect } from 'react'
import '../../App.css'
import HeroSection from '../HeroSection'
import TextHeaderWithLine from '../TextHeaderWithLine'
import PhotoGrid from '../PhotoGrid'
import { listPhotosInFolder, getPhotoThumbURLAspectClass } from '../../services/AWSService';

function Home() {

    const [allPhotoData, setAllPhotoData] = useState([]);

    // Grab all of the fotos in recent favorites
    useEffect(() => {
        const fetchData = async () => {
            try {
                const photoObj = await listPhotosInFolder('recentfavorites');

                // get the URLs of the objects and their thumbnails
                const photoURLPromises = await photoObj.map((photo) => getPhotoThumbURLAspectClass(photo));

                // Wait for all promises to resolve
                const photoURLs = await Promise.all(photoURLPromises);

                setAllPhotoData(photoURLs);
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