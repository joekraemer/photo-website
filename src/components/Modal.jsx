import React, { useEffect } from 'react';
import { Fraction } from 'mathjs';
import './Modal.css'

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


function Modal({ src, onClose, exifData }) {
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

    const apertureRounded = Math.round(exifData.ApertureValue * 10) / 10
    const shutterSpeedFormatted = formatShutterSpeed(exifData.ExposureTime)
    const isoFormatted = formatISO(exifData.ISO);

    return (
        <div className="modal">
            <div className="modal-content">
                <img className="modal-img" src={src} alt="Full Resolution" />
                <div className='modal-button' onClick={onClose}>
                    <i className='fas fa-times' onClick={onClose} />
                </div>
                <div className="exif__data">
                    <p>{shutterSpeedFormatted.n}/{shutterSpeedFormatted.d}   f/{apertureRounded}   ISO {isoFormatted}</p>
                </div>
            </div>
        </div>
    );
}


export default Modal;

