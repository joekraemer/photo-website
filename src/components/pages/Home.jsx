import React from 'react';
import '../../App.css';
import HeroSection from '../HeroSection';
import TextHeaderWithLine from '../TextHeaderWithLine';
import PhotoGrid from '../PhotoGrid';
import useManifest from '../../services/useManifest';

const RECENT_ALBUMS = 6;

function Home() {
    const { manifest } = useManifest();
    // Recent favorites = the cover photo of each of the newest albums.
    const favorites = manifest
        ? manifest.albums.slice(0, RECENT_ALBUMS).map((a) => a.coverPhoto).filter(Boolean)
        : [];

    return (
        <>
            <HeroSection />
            <TextHeaderWithLine title="Recent Favorites" />
            <PhotoGrid photos={favorites} />
        </>
    );
}

export default Home;
