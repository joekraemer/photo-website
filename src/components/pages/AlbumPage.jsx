import React, { useEffect } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import '../../App.css';
import './PhotosPage.css';
import PhotoGrid from '../PhotoGrid';
import useManifest from '../../services/useManifest';
import { formatAlbumDate } from '../../services/photoService';
import useDocumentTitle from '../../hooks/useDocumentTitle';

function AlbumPage() {
    const { slug, photoId } = useParams();
    const navigate = useNavigate();
    const location = useLocation();
    const { manifest, error, loading } = useManifest();
    const album = manifest ? manifest.albums.find((a) => a.slug === slug) : null;
    useDocumentTitle(album ? album.title : manifest ? 'Album not found' : 'Photos');

    const albumPath = `/photos/${slug}`;
    const photoPath = (id) => `${albumPath}/${encodeURIComponent(id)}`;
    // Set on photo URLs this page pushed itself, so Back (or close) returns to the album.
    const pushedHere = Boolean(location.state && location.state.lightbox);
    const photoKnown = Boolean(album && photoId && album.photos.some((p) => p.id === photoId));

    // A shared link opened directly: put the album underneath it in history so
    // Back closes the lightbox instead of leaving the site. Unknown photo ids
    // (removed or re-exported) fall back to the plain album.
    useEffect(() => {
        if (!album || !photoId || pushedHere) return;
        navigate(albumPath, { replace: true });
        if (photoKnown) navigate(photoPath(photoId), { state: { lightbox: true } });
    }, [album, photoId, pushedHere, photoKnown]); // eslint-disable-line react-hooks/exhaustive-deps

    const onOpenChange = (id, { step } = {}) => {
        if (id === null) {
            if (pushedHere) navigate(-1);
            else navigate(albumPath, { replace: true });
        } else {
            // Stepping replaces the entry, so one Back closes the lightbox
            // rather than walking back through every photo viewed.
            navigate(photoPath(id), { replace: Boolean(step && photoId), state: { lightbox: true } });
        }
    };

    if (loading) return <p className="status__text">Loading…</p>;
    if (error) return <p className="status__text">Photos are unavailable right now.</p>;

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
            <PhotoGrid
                photos={album.photos}
                variant="medium"
                openId={pushedHere ? photoId : null}
                onOpenChange={onOpenChange}
            />
        </>
    );
}

export default AlbumPage;
