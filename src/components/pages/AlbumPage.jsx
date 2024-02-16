import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

import '../../App.css'
import { listPhotosInFolder, getPhotoThumbURLAspectClass } from '../../services/AWSService';
import PhotoGrid from '../PhotoGrid';


function AlbumPage() {
    let params = useParams()

    const folderPath = 'portfolio/' + params.folder + '/';
    const [photoKeys, setPhotoKeys] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await listPhotosInFolder(folderPath);

                // remove photos that do not have the word thumbnail in them
                const filteredPhotos = res.filter(photoObj => photoObj.key.includes('thumb'));


                // get the URLs of the objects and their thumbnails
                const photoURLPromises = await filteredPhotos.map((photo) => getPhotoThumbURLAspectClass(photo));

                // Wait for all promises to resolve
                const photoURLs = await Promise.all(photoURLPromises);

                setPhotoKeys(photoURLs);

            } catch (error) {
                console.error('Error fetching data:', error);
            }
        };

        fetchData();
    }, [folderPath]);

    return (
        <>
            <h1>Photos / {params.folder}</h1>
            <PhotoGrid photoSources={photoKeys} />
        </>
    );
}

export default AlbumPage;