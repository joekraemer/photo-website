import React, { useState } from 'react';
import Modal from './Modal'; // Import the Modal component
import exifr from 'exifr';

function Photo({ srcThumb, srcFull }) {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [exifData, setExifData] = useState(null);


    const openModal = async () => {
        // try {
        //     const data = await exifr.parse(srcThumb.href);
        //     setExifData(data);
        // } catch (error) {
        //     console.error('Error reading EXIF data:', error);
        // }

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
                {srcThumb && <img className={`photo__img`} src={srcThumb} alt={`thumbnail-${srcThumb}`} loading="lazy" />}
            </figure >
            {isModalOpen && <Modal src={srcFull} onClose={closeModal} exifData={exifData} />
            }
        </>
    );
}

export default Photo;
