import React, { useState } from 'react';
import Modal from './Modal'; // Import the Modal component

function Photo({ src }) {
    const [isModalOpen, setIsModalOpen] = useState(false);

    const openModal = () => {
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
    };

    // Define different CSS classes based on aspect ratio
    const aspectClass = calculateAspectClass(src);

    return (
        <figure className={`photo__figure`} onClick={openModal}>
            <img className={`photo__img--${aspectClass}`} src={src} alt="Photo" loading="lazy" />
            {isModalOpen && <Modal src={src} onClose={closeModal} />}
        </figure>
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
