import React, { useEffect } from 'react';
import { exifLine } from '../services/photoService';
import './Modal.css';

// Full-screen lightbox: the watermarked large size plus album title and EXIF.
function Modal({ photo, onClose }) {
    useEffect(() => {
        const onKey = (event) => { if (event.key === 'Escape') onClose(); };
        document.addEventListener('keydown', onKey);
        return () => document.removeEventListener('keydown', onKey);
    }, [onClose]);

    const exif = exifLine(photo.exif);

    return (
        <div className="modal" onClick={(event) => { if (event.target === event.currentTarget) onClose(); }}>
            <div className="modal-content">
                <img
                    className="modal-img"
                    src={photo.urls.large}
                    alt={photo.alt}
                    width={photo.width}
                    height={photo.height}
                />
                <div className="modal-button" onClick={onClose} role="button" aria-label="Close">
                    <i className="fas fa-times" />
                </div>
                {(photo.albumTitle || exif) && (
                    <div className="exif__data">
                        {photo.albumTitle && <p className="exif__album">{photo.albumTitle}</p>}
                        {exif && <p>{exif}</p>}
                    </div>
                )}
            </div>
        </div>
    );
}

export default Modal;
