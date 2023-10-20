import React, { useState, useEffect } from 'react';
import Modal from './Modal'; // Import the Modal component
import { retrieveImageFromS3 } from '../services/AWSService.js'; // Import the AWS service

function Photo({ src }) {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [imageData, setImageData] = useState(null);

    const openModal = () => {
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

    useEffect(() => {
        // Load the image from S3 when the component mounts
        retrieveImageFromS3(src)
            .then((imageContent) => {
                setImageData(imageContent);
            })
            .catch((error) => {
                console.error('Error loading image from S3:', error);
            });
    }, [src]);

    const aspectClass = calculateAspectClass(src);

    return (
        <>
            <figure className={`photo__figure`} onClick={(event) => openModal(event)}>
                <img className={`photo__img--${aspectClass}`} src={src} alt="Photo" loading="lazy" />
                {imageData && <img className={`photo__img--${aspectClass}`} src={URL.createObjectURL(imageData)} alt="Photo" loading="lazy" />}
            </figure>
            {isModalOpen && <Modal src={src} onClose={closeModal} />}
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
