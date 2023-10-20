import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './PhotoCard.css';

function PhotoCard(props) {

    const rotationDegree_deg = 20
    const translationAmount_px = 120


    const reversedPhotoPaths = [...props.photopaths].reverse();
    const [isHovered, setIsHovered] = useState(false);

    const srcFanElements = reversedPhotoPaths.map((src, index) => {
        const transformStyle = {
            transform: isHovered
                ? `translateX(${translationAmount_px + index * -translationAmount_px}px) translateY(0px) rotate(${rotationDegree_deg + index * -rotationDegree_deg}deg)`
                : 'translateX(0px) translateY(0px) rotate(0deg)', // Return to normal state
            transition: 'transform 0.5s ease-in-out, opacity 0.5s ease-in-out',
        };

        return (
            <figure
                className={`photo__card__figure ${isHovered ? 'hovered' : ''}`}
                key={index}
                id={`photo__card__figure-${index}`}
                style={transformStyle}
            >
                <img src={src} className={`photo__card__img`} />
            </figure>
        );
    });

    return (
        <>
            <div
                className={`photo__card ${isHovered ? 'hovered' : ''}`}
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
            >
                <Link className='photo__card__link' to={props.paths}>
                    <div className='photo__card__photostack'>
                        {srcFanElements}
                    </div>
                    <h3 className='photo__card__title'> {props.title} </h3>
                </Link>
            </div>
        </>
    );
}

export default PhotoCard;
