import React from 'react';
import { Link, useParams } from 'react-router-dom';
import '../../App.css';
import './PhotosPage.css';
import PhotoGrid from '../PhotoGrid';
import useManifest from '../../services/useManifest';
import { formatAlbumDate } from '../../services/photoService';

function AlbumPage() {
    const { slug } = useParams();
    const { manifest, error, loading } = useManifest();

    if (loading) return <p className="status__text">Loading…</p>;
    if (error) return <p className="status__text">Photos are unavailable right now.</p>;

    const album = manifest.albums.find((a) => a.slug === slug);
    if (!album) {
        return (
            <>
                <h1>Album not found</h1>
                <p><Link to="/photos">Back to all albums</Link></p>
            </>
        );
    }

    return (
        <>
            <h1><Link to="/photos" className="breadcrumb">Photos</Link> / {album.title}</h1>
            {album.date && <p className="album__date">{formatAlbumDate(album.date)}</p>}
            {album.intro && album.intro.split(/\n{2,}/).map((para, i) => (
                <p className="album__intro" key={i}>{para}</p>
            ))}
            <PhotoGrid photos={album.photos} variant="medium" />
        </>
    );
}

export default AlbumPage;
