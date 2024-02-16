import React from 'react';
import Photo from './Photo';
import './PhotoGrid.css'


function PhotoGrid({ photoSources }) {
    // Create arrays to hold rows of vertical and horizontal photos
    const verticalRows = [];
    const horizontalRows = [];
    let currentVerticalRow = [];
    let currentHorizontalRow = [];

    // Iterate through the photoSources and organize them into rows
    photoSources.forEach((src, index) => {
        // src is now the main photo and the thumbnail
        const fullImageUrl = src[0];
        const thumbImageUrl = src[1];
        const aspectClass = src[2]

        if (aspectClass === 'vertical') {
            currentVerticalRow.push(<Photo key={index} src={fullImageUrl} />);
        } else {
            currentHorizontalRow.push(<Photo key={index} src={fullImageUrl} />);
        }

        // Check if it's time to start a new row
        if (aspectClass === 'vertical') {
            if (currentVerticalRow.length === 3 || (currentVerticalRow.length === 2 && index === photoSources.length - 1)) {
                verticalRows.push(currentVerticalRow);
                currentVerticalRow = [];
            }
        } else {
            if (currentHorizontalRow.length === 2 || (currentHorizontalRow.length === 1 && index === photoSources.length - 1)) {
                horizontalRows.push(currentHorizontalRow);
                currentHorizontalRow = [];
            }
        }
    });

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