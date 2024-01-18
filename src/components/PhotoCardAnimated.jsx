import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './PhotoCardAnimated.css';

function PhotoCardAnimated(props) {
    const rotationDegree_deg = 20;
    const translationAmount_em = 2;
    const transitionTime = 0.4;

    const reversedPhotoPaths = [...props.photopaths].reverse();
    const [isHovered, setIsHovered] = useState(false);
    const [zIndexShift, setZIndexShift] = useState(false);

    // Conditionally define inline styles based on screen size
    const isLargeScreen = window.innerWidth > 768;

    const srcFanElements = reversedPhotoPaths.map((src, index) => {
        const zIndex = zIndexShift ? 10 + index : index;

        const handleTransitionEnd = () => {
            if (!isHovered) {
                setZIndexShift(false);
            }
        };

        const boxShadowStyle = isHovered
            ? '1em 1em 1em rgba(0, 0, 0, 0.5)'
            : 'none';

        const transformStyle = {
            transform: isHovered && isLargeScreen
                ? `translateX(${translationAmount_em + index * -translationAmount_em}em) translateY(-1em) rotate(${rotationDegree_deg + index * -rotationDegree_deg}deg)`
                : 'translateX(0px) translateY(0px) rotate(0deg)',
            transition: `transform ${transitionTime}s ease-in-out, box-shadow ${transitionTime}s ease-in-out`,
            zIndex: zIndex,
            boxShadow: isLargeScreen ? boxShadowStyle : 'none',
        };

        return (
            <figure
                className={`photo__card ${isHovered ? 'hovered' : ''}`}
                key={index}
                id={`photo__card-${index}`}
                style={transformStyle}
                onTransitionEnd={() => handleTransitionEnd()}
            >
                <img src={src} alt='cover and sub cards' />
            </figure>
        );
    });

    return (
        <>
            <div
                className={`photo__card ${isHovered ? 'hovered' : ''}`}
                onMouseEnter={() => { setIsHovered(true); setZIndexShift(true); }}
                onMouseLeave={() => setIsHovered(false)}
            >
                <Link to={props.path}>
                    <div className='photo__card__photostack'>
                        {srcFanElements}
                    </div>
                    <h3 className='photo__card__title'> {props.title} </h3>
                </Link>
            </div>
        </>
    );
}

export default PhotoCardAnimated;
