import React, { useEffect, useRef } from 'react';
import { placeholderProps } from '../services/photoService';
import { HOVER_INTENT_MS, prefetchImage } from '../services/prefetch';

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
// Opening the lightbox is up to the grid (onOpen), which knows the neighbours.
function Photo({ photo, variant = 'thumb', perRow = 1, onOpen, buttonRef }) {
    const hoverTimer = useRef(null);
    useEffect(() => () => clearTimeout(hoverTimer.current), []);

    // Start the lightbox's large image when someone is about to click: mouse
    // resting on the photo, a finger touching it, or keyboard focus.
    const prefetchLarge = () => prefetchImage(photo.urls && photo.urls.large);
    const onPointerEnter = (event) => {
        if (event.pointerType !== 'mouse') return;
        clearTimeout(hoverTimer.current);
        hoverTimer.current = setTimeout(prefetchLarge, HOVER_INTENT_MS);
    };
    const onPointerLeave = () => clearTimeout(hoverTimer.current);

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
                    onClick={onOpen}
                    onPointerEnter={onPointerEnter}
                    onPointerLeave={onPointerLeave}
                    onTouchStart={prefetchLarge}
                    onFocus={prefetchLarge}
                    ref={buttonRef}
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
                        {...placeholderProps(photo)}
                    />
                </button>
            </figure>
        </>
    );
}

export default Photo;
