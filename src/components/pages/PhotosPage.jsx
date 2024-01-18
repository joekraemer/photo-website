import React, { useState, useEffect } from 'react'
import '../../App.css'
import './PhotosPage.css'
import PhotoCard from '../PhotoCard'
import { listFoldersInDirectory, listPhotosInFolder } from '../../services/AWSService';


function PhotosPage() {

    const bucketName = 'photo-website-photos';
    const [bucketFolders, setBucketFolders] = useState([]);
    const [allPhotoData, setAllPhotoData] = useState([]);

    // Grab all of the sub folders in the portfolio folder
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

    const fetchTitlePhotosForFolder = async (folder) => {
        try {
            const photos = await listPhotosInFolder(bucketName, `portfolio/${folder}`);

            // We will look for a photo called "Cover"


            // If there is no Cover photo, use the first photo
            const coverPhotoPath = photos.length > 0 ? photos[0] : null;
            return { folder, coverPhotoPath };
        } catch (error) {
            console.error(`Error fetching photos for ${folder}:`, error);
            return { folder, coverPhotoPath: null };
        }
    };

    const fetchAllPhotos = async () => {
        const photoDataPromises = bucketFolders.map((folder) => fetchTitlePhotosForFolder(folder));
        const allPhotoData = await Promise.all(photoDataPromises);
        return allPhotoData;
    };

    useEffect(() => {
        const fetchAndSetPhotos = async () => {
            const allPhotoData = await fetchAllPhotos();
            // Set state with the fetched photo data
            // Update this logic based on your PhotoCard component structure
            console.log(allPhotoData);
            setAllPhotoData(allPhotoData);
        };

        if (bucketFolders.length > 0) {
            fetchAndSetPhotos();
        }
    }, [bucketFolders]);

    return (
        <>
            <h1>Photos</h1>
            <div className="photo-card-container">
                {/* Render PhotoCards based on fetched data */}
                {allPhotoData.map((data) => (
                    <PhotoCard
                        key={data.folder}
                        photopath={`${data.coverPhotoPath}`} // Adjust the path as needed
                        title={data.folder}
                        path={data.folder}
                    />
                ))}
            </div>
        </>
    );
}

export default PhotosPage;