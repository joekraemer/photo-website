import React, { useState, useEffect } from 'react';

import '../../App.css'
import { getBucketContents } from '../../services/AWSService';
import Photo from '../Photo';
import PhotoGrid from '../PhotoGrid';


function SouthAfrica() {
    const bucketName = 'photo-website-photos';
    const [photoKeys, setPhotoKeys] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res2 = await getBucketContents(bucketName);

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
            <h1>Photos / South Africa</h1>
            <PhotoGrid photoSources={photoKeys} />
        </>
    );
}

export default SouthAfrica;