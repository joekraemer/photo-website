import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

import '../../App.css'
import { listPhotosInFolder } from '../../services/AWSService';
import PhotoGrid from '../PhotoGrid';


function AlbumPage() {
    let params = useParams()

    const folderPath = 'portfolio/' + params.folder + '/';
    const [photoKeys, setPhotoKeys] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await listPhotosInFolder(folderPath);

                setPhotoKeys(res);
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        };

        fetchData();
    }, []);

    return (
        <>
            <h1>Photos / {params.folder}</h1>
            <PhotoGrid photoSources={photoKeys} />
        </>
    );
}

export default AlbumPage;