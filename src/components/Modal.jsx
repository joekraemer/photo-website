import React, { useEffect } from 'react';
import './Modal.css'

function Modal({ src, onClose }) {
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

    return (
        <div className="modal">
            <div className="modal-content">
                <img className="modal-img" src={src} alt="Full Resolution Photo" />
                <div className='modal-button' onClick={onClose}>
                    <i className='fas fa-times' onClick={onClose} />
                </div>

            </div>
        </div>
    );
}


export default Modal;

