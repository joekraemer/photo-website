import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { exifLine, placeholderProps } from '../services/photoService';
import { swipeDirection } from '../services/lightboxNav';
import './Modal.css';

// Full-screen lightbox: the watermarked large size plus its EXIF.
// Left/Right arrows and horizontal swipes move to prevPhoto/nextPhoto.
// previewSrc is the grid's already-downloaded copy of this photo, if any. It is
// drawn underneath at once and removed when the large image has loaded.
function Modal({ photo, previewSrc, prevPhoto, nextPhoto, onPrev, onNext, onClose }) {
    const closeRef = useRef(null);
    const [loadedId, setLoadedId] = useState(null);
    const showPreview = Boolean(previewSrc) && loadedId !== photo.id;
    const dialogRef = useRef(null);
    const touchStart = useRef(null);
    const exifRef = useRef(null);
    const [exifTooWide, setExifTooWide] = useState(false);

    // The caption has one line in the frame's bottom border. If the full line
    // doesn't fit the frame's width, fall back to the line without the lens.
    // Re-measured per photo and on window resize.
    useLayoutEffect(() => {
        const measure = () => {
            setExifTooWide(false);
            requestAnimationFrame(() => {
                const el = exifRef.current;
                if (el) setExifTooWide(el.scrollWidth > el.clientWidth + 1);
            });
        };
        measure();
        window.addEventListener('resize', measure);
        return () => window.removeEventListener('resize', measure);
    }, [photo.id]);

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
    // Same line without the lens, for frames too narrow to fit the full one.
    const exifShort = photo.exif ? exifLine({ ...photo.exif, lens: null }) : '';
    // With a preview underneath, the large image stays transparent while it
    // loads so the preview shows through; otherwise it shows the colour.
    const placeholder = previewSrc ? {} : placeholderProps(photo);
    const onLargeLoad = (event) => {
        if (placeholder.onLoad) placeholder.onLoad(event);
        setLoadedId(photo.id);
    };
    const boxStyle = photo.width && photo.height
        ? { '--aspect': photo.width / photo.height, '--natural-w': `${photo.width}px` }
        : {};

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
                {showPreview && (
                    <img
                        key={`preview-${photo.id}`}
                        className="modal-preview"
                        src={previewSrc}
                        alt=""
                        aria-hidden="true"
                    />
                )}
                <img
                    key={photo.id}
                    className="modal-img"
                    src={photo.urls.large}
                    alt={photo.alt}
                    width={photo.width}
                    height={photo.height}
                    {...placeholder}
                    onLoad={onLargeLoad}
                    style={{ ...placeholder.style, ...boxStyle }}
                />
                <button type="button" className="modal-button" onClick={onClose} aria-label="Close" ref={closeRef}>
                    <i className="fas fa-times" aria-hidden="true" />
                </button>
                {prevPhoto && (
                    <button type="button" className="modal-arrow modal-arrow--prev" onClick={onPrev} aria-label="Previous photo">
                        <i className="fas fa-chevron-left" aria-hidden="true" />
                    </button>
                )}
                {nextPhoto && (
                    <button type="button" className="modal-arrow modal-arrow--next" onClick={onNext} aria-label="Next photo">
                        <i className="fas fa-chevron-right" aria-hidden="true" />
                    </button>
                )}
                {exif && (
                    <div className="exif__data">
                        <p ref={exifRef} title={exif}>{exifTooWide && exifShort ? exifShort : exif}</p>
                    </div>
                )}
            </div>
        </div>
    );
}

export default Modal;
