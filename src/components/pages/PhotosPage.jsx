import React, { useState, useEffect } from 'react'
import '../../App.css'
import './PhotosPage.css'
import PhotoCard from '../PhotoCard'
import { listFoldersInDirectory } from '../../services/AWSService';


function PhotosPage() {

    const bucketName = 'photo-website-photos';
    const [bucketFolders, setBucketFolders] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const folderpaths = await listFoldersInDirectory(bucketName, 'portfolio');

                // removes the leading '/portfolio/' and the trailing '/' so we only have the sub folder name
                const foldernames = folderpaths.map((str) => str.replace(/^portfolio\//, '').replace(/\/$/, ''));

                setBucketFolders(foldernames);
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        };

        fetchData();
    }, [bucketName]);

    return (
        <>
            <h1>Photos</h1>
            <div className="photo-card-container">
                <PhotoCard
                    photopaths={["/photos/portfolio/South Korea/DSC09123.jpg",
                        "/photos/portfolio/South Korea/DSC00021.jpg",
                        "/photos/portfolio/South Korea/DSC00085.jpg",]}
                    title="South Korea"
                    path='/southkorea'
                />
                <PhotoCard
                    photopaths={["/photos/portfolio/South Africa/DSC02715.jpg",
                        "/photos/recentfavorites/DSC07277.jpg",
                        "/photos/portfolio/South Korea/DSC00085.jpg"]}
                    title="South Africa"
                    path='/southafrica'
                />
                <PhotoCard
                    photopaths={["/photos/recentfavorites/DSC07277.jpg",
                        "/photos/recentfavorites/DSC09335.jpg",
                        "/photos/recentfavorites/DSC00266.jpg",]}
                    title="Tanzania"
                    path='/southkorea'
                />
                <PhotoCard
                    photopaths={["/photos/portfolio/South Korea/DSC00085.jpg",
                        "/photos/recentfavorites/DSC09335.jpg",
                        "/photos/recentfavorites/DSC00266.jpg",]}
                    title="Another Place"
                    path='/southkorea'
                />
                <PhotoCard
                    photopaths={["/photos/recentfavorites/DSC09335.jpg",
                        "/photos/portfolio/South Korea/DSC00085.jpg",
                        "/photos/portfolio/South Africa/DSC02715.jpg",]}
                    title="North Korea"
                    path='/southkorea'
                />
                <PhotoCard
                    photopaths={["/photos/portfolio/South Korea/DSC00021.jpg",
                        "/photos/portfolio/South Korea/DSC09123.jpg",
                        "/photos/portfolio/South Korea/DSC00085.jpg",]}
                    title="Taiwan"
                    path='/southkorea'
                />
            </div>
        </>
    )
}

export default PhotosPage