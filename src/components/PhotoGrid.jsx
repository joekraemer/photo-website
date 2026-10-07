import React from 'react';
import Photo from './Photo';
import './PhotoGrid.css';

// Rows of three verticals or two horizontals, interleaved, using the manifest's
// aspect ratio instead of loading every image to measure it.
function PhotoGrid({ photos, variant = 'thumb' }) {
    const verticalRows = [];
    const horizontalRows = [];
    let vertical = [];
    let horizontal = [];

    photos.forEach((photo) => {
        const cell = <Photo key={photo.id} photo={photo} variant={variant} />;
        if ((photo.aspect || 1) < 1) {
            vertical.push(cell);
            if (vertical.length === 3) { verticalRows.push(vertical); vertical = []; }
        } else {
            horizontal.push(cell);
            if (horizontal.length === 2) { horizontalRows.push(horizontal); horizontal = []; }
        }
    });
    if (vertical.length) verticalRows.push(vertical);
    if (horizontal.length) horizontalRows.push(horizontal);

    const rows = [];
    const maxLength = Math.max(verticalRows.length, horizontalRows.length);
    for (let i = 0; i < maxLength; i++) {
        if (verticalRows[i]) rows.push(verticalRows[i]);
        if (horizontalRows[i]) rows.push(horizontalRows[i]);
    }

    return (
        <div className="photo-grid">
            {rows.map((row, index) => (
                <div className="photo-row" key={index}>
                    {row}
                </div>
            ))}
        </div>
    );
}

export default PhotoGrid;
