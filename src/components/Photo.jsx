import React from 'react';

function Photo({ src }) {
    // Calculate the aspect ratio of the photo
    const img = new Image();
    img.src = src;
    const aspectRatio = img.width / img.height;

    // Define different CSS classes based on aspect ratio
    const aspectClass = aspectRatio >= 1 ? 'horizontal' : 'vertical';

    return (
        <figure className={`photo__figure`}>
            <img className={`photo__img--${aspectClass}`} src={src} alt="Photo" />
        </figure>
    );
}

export default Photo;