import React, { useEffect, useRef, useState } from 'react';
import Photo from './Photo';
import Modal from './Modal';
import { buildRows, stepIndex } from '../services/lightboxNav';
import './PhotoGrid.css';

// The grid owns the lightbox so it can move between photos in the order they
// appear on screen (row by row, left to right).
function PhotoGrid({ photos, variant = 'thumb' }) {
    const rows = buildRows(photos);
    const ordered = rows.flat();

    const [openIndex, setOpenIndex] = useState(null);
    const lastIndex = useRef(null);
    const buttons = useRef([]);

    // After closing, put focus on the photo the viewer ended on, not the one
    // they first opened. Runs after the lightbox's own focus cleanup.
    useEffect(() => {
        if (openIndex !== null || lastIndex.current === null) return;
        const button = buttons.current[lastIndex.current];
        if (button) button.focus();
    }, [openIndex]);

    const open = (index) => { lastIndex.current = index; setOpenIndex(index); };
    const go = (step) => {
        const next = openIndex === null ? null : stepIndex(openIndex, step, ordered.length);
        if (next !== null) open(next);
    };

    let position = 0;
    return (
        <div className="photo-grid">
            {rows.map((row, index) => (
                <div className="photo-row" key={index}>
                    {row.map((photo) => {
                        const i = position++;
                        return (
                            <Photo
                                key={photo.id}
                                photo={photo}
                                variant={variant}
                                perRow={row.length}
                                onOpen={() => open(i)}
                                buttonRef={(el) => { buttons.current[i] = el; }}
                            />
                        );
                    })}
                </div>
            ))}
            {openIndex !== null && ordered[openIndex] && (
                <Modal
                    photo={ordered[openIndex]}
                    prevPhoto={ordered[openIndex - 1]}
                    nextPhoto={ordered[openIndex + 1]}
                    onPrev={() => go(-1)}
                    onNext={() => go(1)}
                    onClose={() => setOpenIndex(null)}
                />
            )}
        </div>
    );
}

export default PhotoGrid;
