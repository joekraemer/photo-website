import React, { useState } from 'react';
import Modal from './Modal';

// One photo in a grid. Both variants offer thumb and medium through srcset so a
// photo shown wide (e.g. alone in its row) gets the medium size instead of a
// stretched thumb. variant="medium" (album view) also defaults src to medium.
function Photo({ photo, variant = 'thumb' }) {
    const [isModalOpen, setIsModalOpen] = useState(false);

    const imgProps = {
        src: variant === 'medium' ? photo.urls.medium : photo.urls.thumb,
        srcSet: `${photo.urls.thumb} 500w, ${photo.urls.medium} 1600w`,
        sizes: '(max-width: 768px) 100vw, 50vw',
    };

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
