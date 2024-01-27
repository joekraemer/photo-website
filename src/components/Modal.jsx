import React, { useState, useEffect } from 'react'
import { Fraction } from 'mathjs';
import './Modal.css'
import { retrieveImageFromS3 } from '../services/AWSService';

function formatShutterSpeed(shutterSpeed) {
    if (shutterSpeed > 1) {
        // Format as a decimal with one decimal place
        return shutterSpeed.toFixed(1);
    } else {
        // Convert to a fraction
        return Fraction(shutterSpeed);
    }
}


function formatISO(isoValue) {
    if (isoValue < 200) {
        return Math.round(isoValue / 25) * 25;
    } else {
        return Math.round(isoValue / 100) * 100;
    }
}


function findHighResolutionPhotoLocation(src) {
    // Takes a source string in the thumbnail format and tries to find a high resolution photo that is higher in the folder

    // Check if the path contains "/thumbs/" and ends with "_thumb.jpg"
    const regex = /\/thumbs\/(.+)_thumb\.jpg$/;
    const match = src.match(regex);

    if (match) {
        // If the regex matches, construct the new path without "_thumb" and "/thumbs/"
        const folderPath = match[1];
        const newPath = src.replace(`/thumbs/${folderPath}_thumb.jpg`, `/${folderPath}.jpg`);
        return newPath;
    } else {
        // If the regex doesn't match, return null
        return src;
    }
}


function Modal({ src, onClose, exifData }) {
    const [imageSrc, setImageSrc] = useState(null);


    useEffect(() => {
        // Function to handle clicks outside of the modal
        function handleClickOutside(event) {
            const modalContent = document.querySelector('.modal-content');
            if (modalContent && !modalContent.contains(event.target)) {
                onClose(); // Close the modal if clicked outside
            }
        }

        // Add a click event listener on the document
        document.addEventListener('click', handleClickOutside);

        // Clean up the event listener when the component unmounts
        return () => {
            document.removeEventListener('click', handleClickOutside);
        };
    }, [onClose]);

    // Need to take the src and find the full res version of the photo
    const modalSrc = findHighResolutionPhotoLocation(src.key);

    useEffect(() => {
        // Load the image from S3 when the component mounts
        retrieveImageFromS3(modalSrc)
            .then((srcObj) => {
                setImageSrc(srcObj.url);
            })
            .catch((error) => {
                console.error('Error loading image from S3:', error);
            });
    }, [modalSrc]);

    const apertureRounded = exifData ? Math.round(exifData.ApertureValue * 10) / 10 : null;
    const shutterSpeedFormatted = exifData ? formatShutterSpeed(exifData.ExposureTime) : null;
    const isoFormatted = exifData ? formatISO(exifData.ISO) : null;

    return (
        <div className="modal">
            <div className="modal-content">
                <img className="modal-img" src={imageSrc} alt="Full Resolution" />
                <div className='modal-button' onClick={onClose}>
                    <i className='fas fa-times' onClick={onClose} />
                </div>
                {exifData && (
                    <div className="exif__data">
                        <p>{shutterSpeedFormatted.n}/{shutterSpeedFormatted.d}   f/{apertureRounded}   ISO {isoFormatted}</p>
                    </div>
                )}
            </div>
        </div>
    );
}


export default Modal;

