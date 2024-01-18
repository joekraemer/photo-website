import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { retrieveImageFromS3 } from '../services/AWSService.js'; // Import the AWS service
import './PhotoCard.css';

function PhotoCard(props) {
    const [imageSrc, setImageSrc] = useState(null);

    useEffect(() => {
        // Load the image from S3 when the component mounts
        retrieveImageFromS3(props.photopath)
            .then((imageURL) => {
                setImageSrc(imageURL);
            })
            .catch((error) => {
                console.error('Error loading image from S3:', error);
            });
    }, [props.photopath]);

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
