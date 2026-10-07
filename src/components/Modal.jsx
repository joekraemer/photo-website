import React, { useEffect, useRef } from 'react';
import { exifLine } from '../services/photoService';
import './Modal.css';

// Full-screen lightbox: the watermarked large size plus album title and EXIF.
function Modal({ photo, onClose }) {
    const closeRef = useRef(null);

    // Move focus into the dialog and give it back to the opener on close.
    useEffect(() => {
        const opener = document.activeElement;
        if (closeRef.current) closeRef.current.focus();
        return () => { if (opener && opener.focus) opener.focus(); };
    }, []);

    useEffect(() => {
        const onKey = (event) => { if (event.key === 'Escape') onClose(); };
        document.addEventListener('keydown', onKey);
        return () => document.removeEventListener('keydown', onKey);
    }, [onClose]);

    const exif = exifLine(photo.exif);

    return (
        <div
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-label={photo.alt}
            onClick={(event) => { if (event.target === event.currentTarget) onClose(); }}
        >
            <div className="modal-content">
                <img
                    className="modal-img"
                    src={photo.urls.large}
                    alt={photo.alt}
                    width={photo.width}
                    height={photo.height}
                />
                <button type="button" className="modal-button" onClick={onClose} aria-label="Close" ref={closeRef}>
                    <i className="fas fa-times" aria-hidden="true" />
                </button>
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
