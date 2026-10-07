import React, { useState } from 'react';
import Modal from './Modal';

// Grid layout numbers from App.css (.main__container) and PhotoGrid.css (.photo-row).
const PAGE_PADDING_PX = 96;   // 3em each side
const CONTENT_MAX_PX = 1120;
const ROW_GAP_PX = 24;        // 1.5em
const STACK_BREAKPOINT_PX = 768;

// The width the browser will actually draw a photo at, so srcset can pick the
// smallest file that is sharp enough. Rows stack to one column on phones.
export function gridSizes(perRow = 1) {
    const gaps = (perRow - 1) * ROW_GAP_PX;
    const wide = Math.round((CONTENT_MAX_PX - gaps) / perRow);
    return [
        `(max-width: ${STACK_BREAKPOINT_PX}px) calc(100vw - ${PAGE_PADDING_PX}px)`,
        `(max-width: ${CONTENT_MAX_PX + PAGE_PADDING_PX}px) calc((100vw - ${PAGE_PADDING_PX + gaps}px) / ${perRow})`,
        `${wide}px`,
    ].join(', ');
}

// One photo in a grid. Both variants offer thumb and medium through srcset so a
// photo shown wide (e.g. alone in its row) gets the medium size instead of a
// stretched thumb. variant="medium" (album view) also defaults src to medium.
function Photo({ photo, variant = 'thumb', perRow = 1 }) {
    const [isModalOpen, setIsModalOpen] = useState(false);

    const imgProps = {
        src: variant === 'medium' ? photo.urls.medium : photo.urls.thumb,
        srcSet: `${photo.urls.thumb} 500w, ${photo.urls.medium} 1600w`,
        sizes: gridSizes(perRow),
    };

    return (
        <>
            <figure className="photo__figure">
                <button
                    type="button"
                    className="photo__button"
                    onClick={() => setIsModalOpen(true)}
                    aria-label={`Open ${photo.alt}`}
                >
                    <img
                        className="photo__img"
                        alt={photo.alt}
                        width={photo.width}
                        height={photo.height}
                        loading="lazy"
                        decoding="async"
                        {...imgProps}
                    />
                </button>
            </figure>
            {isModalOpen && <Modal photo={photo} onClose={() => setIsModalOpen(false)} />}
        </>
    );
}

export default Photo;
