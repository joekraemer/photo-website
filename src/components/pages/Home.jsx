import React from 'react';
import '../../App.css';
import './PhotosPage.css';
import HeroSection from '../HeroSection';
import TextHeaderWithLine from '../TextHeaderWithLine';
import PhotoGrid from '../PhotoGrid';
import useManifest from '../../services/useManifest';

const RECENT_ALBUMS = 6;

function Home() {
    const { manifest, error, loading } = useManifest();
    // Recent favorites = the cover photo of each of the newest albums.
    const favorites = manifest
        ? manifest.albums.slice(0, RECENT_ALBUMS).map((a) => a.coverPhoto).filter(Boolean)
        : [];

    let body;
    if (loading) body = <p className="status__text">Loading…</p>;
    else if (error) body = <p className="status__text">Photos are unavailable right now.</p>;
    else if (favorites.length === 0) body = <p className="status__text">No albums yet.</p>;
    else body = <PhotoGrid photos={favorites} />;

    return (
        <>
            <HeroSection />
            <TextHeaderWithLine title="Recent Favorites" />
            {body}
        </>
    );
}

export default Home;
