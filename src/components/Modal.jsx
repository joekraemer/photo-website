import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { exifLine, placeholderProps } from '../services/photoService';
import { swipeDirection } from '../services/lightboxNav';
import { prefetchImage } from '../services/prefetch';
import './Modal.css';

const SPINNER_DELAY_MS = 300;

// Full-screen lightbox: the watermarked large size plus its EXIF.
// Left/Right arrows and horizontal swipes move to prevPhoto/nextPhoto.
function Modal({ photo, prevPhoto, nextPhoto, onPrev, onNext, onClose }) {
    const closeRef = useRef(null);
    const dialogRef = useRef(null);
    const touchStart = useRef(null);
    const exifRef = useRef(null);
    const [exifTooWide, setExifTooWide] = useState(false);
    const imgRef = useRef(null);
    const [showSpinner, setShowSpinner] = useState(false);

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
            if (p && p.urls) prefetchImage(p.urls.large);
        });
    }, [prevPhoto, nextPhoto]);

    // A spinner over the placeholder colour, but only if the photo is still
    // missing after SPINNER_DELAY_MS, so quick loads never flash one.
    useEffect(() => {
        setShowSpinner(false);
        const img = imgRef.current;
        if (!img || (img.complete && img.naturalWidth > 0)) return undefined;
        const timer = setTimeout(() => setShowSpinner(true), SPINNER_DELAY_MS);
        const done = () => { clearTimeout(timer); setShowSpinner(false); };
        img.addEventListener('load', done);
        img.addEventListener('error', done);
        return () => {
            clearTimeout(timer);
            img.removeEventListener('load', done);
            img.removeEventListener('error', done);
        };
    }, [photo.id]);

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
    const placeholder = placeholderProps(photo);
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
                <img
                    key={photo.id}
                    ref={imgRef}
                    className="modal-img"
                    src={photo.urls.large}
                    alt={photo.alt}
                    width={photo.width}
                    height={photo.height}
                    {...placeholder}
                    style={{ ...placeholder.style, ...boxStyle }}
                />
                {showSpinner && (
                    <div className="modal-spinner" role="status">
                        <span className="modal-spinner__ring" aria-hidden="true" />
                        <span className="visually-hidden">Loading photo</span>
                    </div>
                )}
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
