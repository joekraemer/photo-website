import React, { useEffect, useRef } from 'react';
import { exifLine } from '../services/photoService';
import './Modal.css';

// Full-screen lightbox: the watermarked large size plus its EXIF.
function Modal({ photo, onClose }) {
    const closeRef = useRef(null);
    const dialogRef = useRef(null);

    // Move focus into the dialog and give it back to the opener on close.
    useEffect(() => {
        const opener = document.activeElement;
        if (closeRef.current) closeRef.current.focus();
        return () => { if (opener && opener.focus) opener.focus(); };
    }, []);

    // Escape closes; Tab and Shift+Tab stay inside the dialog.
    useEffect(() => {
        const onKey = (event) => {
            if (event.key === 'Escape') { onClose(); return; }
            if (event.key !== 'Tab' || !dialogRef.current) return;
            const focusable = dialogRef.current.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            if (focusable.length === 0) { event.preventDefault(); return; }
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            const inside = dialogRef.current.contains(document.activeElement);
            if (event.shiftKey && (document.activeElement === first || !inside)) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && (document.activeElement === last || !inside)) {
                event.preventDefault();
                first.focus();
            }
        };
        document.addEventListener('keydown', onKey);
        return () => document.removeEventListener('keydown', onKey);
    }, [onClose]);

    const exif = exifLine(photo.exif);

    return (
        <div
            className="modal"
            ref={dialogRef}
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
                {exif && (
                    <div className="exif__data">
                        <p>{exif}</p>
                    </div>
                )}
            </div>
        </div>
    );
}

export default Modal;
