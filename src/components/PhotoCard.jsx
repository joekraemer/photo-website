import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getUrl } from 'aws-amplify/storage';
import './PhotoCard.css';

function PhotoCard(props) {
    const [imageSrc, setImageSrc] = useState(null);

    useEffect(() => {
        // Load the image from S3 when the component mounts
        getUrl(props.photoObj)
            .then((res) => {
                setImageSrc(res.url);
            })
            .catch((error) => {
                console.error('Error loading image from S3:', error);
            });
    }, [props.photoObj]);

    return (
        <>
            <div className={`photo__card`} >
                <Link to={props.path}>
                    <figure className={`photo__card`} >
                        <img src={imageSrc} alt='cover and sub cards' />
                    </figure>
                    <h3 className='photo__card__title'> {props.title} </h3>
                </Link>
            </div>
        </>
    );
}

export default PhotoCard;
