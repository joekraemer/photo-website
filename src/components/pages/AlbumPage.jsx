import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

import '../../App.css'
import { getFolderContents } from '../../services/AWSService';
import PhotoGrid from '../PhotoGrid';


function AlbumPage() {
    let params = useParams()

    const bucketName = 'photo-website-photos'
    const folderPath = 'portfolio/' + params.folder + '/';
    const [photoKeys, setPhotoKeys] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res2 = await getFolderContents(bucketName, folderPath);

                const keys = res2.map(obj => obj.Key);
                setPhotoKeys(keys);
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        };

        fetchData();
    }, [bucketName]);

    return (
        <>
            <h1>Photos / {params.folder}</h1>
            <PhotoGrid photoSources={photoKeys} />
        </>
    );
}

export default AlbumPage;