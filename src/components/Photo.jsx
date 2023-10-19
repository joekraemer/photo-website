import React, { useState } from 'react';
import Modal from './Modal'; // Import the Modal component

function Photo({ src }) {
    const [isModalOpen, setIsModalOpen] = useState(false);

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


    const aspectClass = calculateAspectClass(src);

    return (
        <>
            <figure className={`photo__figure`} onClick={(event) => openModal(event)}>
                <img className={`photo__img--${aspectClass}`} src={src} alt="Photo" loading="lazy" />
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
