import React from 'react';
import '../../App.css';
import './PhotosPage.css';
import PhotoCard from '../PhotoCard';
import useManifest from '../../services/useManifest';

function PhotosPage() {
    const { manifest, error, loading } = useManifest();

    return (
        <>
            <h1>Photos</h1>
            {loading && <p className="status__text">Loading…</p>}
            {error && <p className="status__text">Photos are unavailable right now.</p>}
            {manifest && (
                <div className="photo-card-container">
                    {manifest.albums.map((album) => (
                        <PhotoCard key={album.slug} album={album} />
                    ))}
                </div>
            )}
        </>
    );
}

export default PhotosPage;
