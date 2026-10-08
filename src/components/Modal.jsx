import React, { useEffect, useRef } from 'react';
import { exifLine } from '../services/photoService';
import { swipeDirection } from '../services/lightboxNav';
import './Modal.css';

// Full-screen lightbox: the watermarked large size plus its EXIF.
// Left/Right arrows and horizontal swipes move to prevPhoto/nextPhoto.
function Modal({ photo, prevPhoto, nextPhoto, onPrev, onNext, onClose }) {
    const closeRef = useRef(null);
    const dialogRef = useRef(null);
    const touchStart = useRef(null);

    // Move focus into the dialog and give it back to the opener on close.
    useEffect(() => {
        const opener = document.activeElement;
        if (closeRef.current) closeRef.current.focus();
        return () => { if (opener && opener.focus) opener.focus(); };
    }, []);

    // Fetch the neighbours' large images now so stepping to them is instant.
    useEffect(() => {
        [prevPhoto, nextPhoto].forEach((p) => {
            if (p && p.urls && p.urls.large) new Image().src = p.urls.large;
        });
    }, [prevPhoto, nextPhoto]);

    // Escape closes; arrows step; Tab and Shift+Tab stay inside the dialog.
    useEffect(() => {
        const onKey = (event) => {
            if (event.key === 'Escape') { onClose(); return; }
            if (event.key === 'ArrowLeft' && prevPhoto && onPrev) { event.preventDefault(); onPrev(); return; }
            if (event.key === 'ArrowRight' && nextPhoto && onNext) { event.preventDefault(); onNext(); return; }
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
    }, [onClose, onPrev, onNext, prevPhoto, nextPhoto]);

    // One finger only, so pinch-zoom on a phone is left alone.
    const onTouchStart = (event) => {
        touchStart.current = event.touches.length === 1
            ? { x: event.touches[0].clientX, y: event.touches[0].clientY }
            : null;
    };
    const onTouchEnd = (event) => {
        const start = touchStart.current;
        touchStart.current = null;
        if (!start || event.changedTouches.length !== 1) return;
        const t = event.changedTouches[0];
        const dir = swipeDirection(t.clientX - start.x, t.clientY - start.y);
        if (dir === -1 && prevPhoto && onPrev) onPrev();
        if (dir === 1 && nextPhoto && onNext) onNext();
    };

    const exif = exifLine(photo.exif);

    return (
        <div
            className="modal"
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-label={photo.alt}
            onClick={(event) => { if (event.target === event.currentTarget) onClose(); }}
            onTouchStart={onTouchStart}
            onTouchEnd={onTouchEnd}
        >
            <div className="modal-content">
                <img
                    key={photo.id}
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
