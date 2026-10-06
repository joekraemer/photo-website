import React, { useState } from 'react';
import Modal from './Modal';

// One photo in a grid. variant="thumb" (overview grids) or "medium" (album view,
// with a srcset so small screens can still take the thumb).
function Photo({ photo, variant = 'thumb' }) {
    const [isModalOpen, setIsModalOpen] = useState(false);

    const imgProps = variant === 'medium'
        ? {
            src: photo.urls.medium,
            srcSet: `${photo.urls.thumb} 500w, ${photo.urls.medium} 1600w`,
            sizes: '(max-width: 768px) 100vw, 50vw',
        }
        : { src: photo.urls.thumb };

    return (
        <>
            <figure className="photo__figure" onClick={() => setIsModalOpen(true)}>
                <img
                    className="photo__img"
                    alt={photo.alt}
                    width={photo.width}
                    height={photo.height}
                    loading="lazy"
                    decoding="async"
                    {...imgProps}
                />
            </figure>
            {isModalOpen && <Modal photo={photo} onClose={() => setIsModalOpen(false)} />}
        </>
    );
}

export default Photo;
