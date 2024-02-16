import React, { useState } from 'react';
import Modal from './Modal'; // Import the Modal component
import exifr from 'exifr';

function Photo({ src }) {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [exifData, setExifData] = useState(null);


    const openModal = async () => {
        try {
            const data = await exifr.parse(src.href);
            setExifData(data);
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

    return (
        <>
            <figure className={`photo__figure`} onClick={(event) => openModal(event)}>
                {src && <img className={`photo__img`} src={src} alt={`thumbnail-${src}`} loading="lazy" />}
            </figure >
            {isModalOpen && <Modal src={src} onClose={closeModal} exifData={exifData} />
            }
        </>
    );
}

export default Photo;
