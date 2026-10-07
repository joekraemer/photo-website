import React from 'react';
import { Link } from 'react-router-dom';
import './PhotosPage.css';
import useDocumentTitle from '../../hooks/useDocumentTitle';

// Plain text page used for unknown URLs and for sections that are not built yet.
function MessagePage({ title, message }) {
    useDocumentTitle(title);
    return (
        <>
            <h1>{title}</h1>
            <p className="status__text">{message}</p>
            <p className="status__text"><Link to="/">Back to the home page</Link></p>
        </>
    );
}

export function NotFound() {
    return <MessagePage title="Page not found" message="There is nothing at this address." />;
}

export function Videos() {
    return <MessagePage title="Videos" message="Videos are coming soon." />;
}

export default MessagePage;
