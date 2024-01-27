import React, { useState, useEffect } from 'react';
import Modal from './Modal'; // Import the Modal component
import { getUrl } from 'aws-amplify/storage';
import exifr from 'exifr';

function Photo({ src }) {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [exifData, setExifData] = useState(null);
    const [imageSrc, setImageSrc] = useState(null);


    const openModal = async () => {
        try {
            // const data = await exifr.parse(imageSrc.href);
            // setExifData(data);
        } catch (error) {
            console.error('Error reading EXIF data:', error);
        }

        console.log('open modal');
        setIsModalOpen(true);
    };

    const closeModal = (event) => {
        console.log('close modal attempt');
        if (event && event.target === event.currentTarget) {
            setIsModalOpen(false);
            console.log('close modal set');
        }
    };

    useEffect(async () => {
        // Load the image from S3 when the component mounts
        getUrl(src)
            .then((res) => {
                setImageSrc(res.url);
            })
            .catch((error) => {
                console.error('Error loading image from S3:', error);
            });
    }, [src]);

    const aspectClass = calculateAspectClass(src);

    return (
        <>
            <figure className={`photo__figure`} onClick={(event) => openModal(event)}>
                {imageSrc && <img className={`photo__img--${aspectClass}`} src={imageSrc} alt={`thumbnail-${src}`} loading="lazy" />}
            </figure >
            {isModalOpen && <Modal src={src} onClose={closeModal} exifData={exifData} />
            }
        </>
    );
}


function calculateAspectClass(src) {
    // Calculate the aspect ratio of the photo
    const img = new Image();
    img.src = src;
    const aspectRatio = img.width / img.height;

    return aspectRatio >= 1 ? 'horizontal' : 'vertical';
}

export default Photo;
