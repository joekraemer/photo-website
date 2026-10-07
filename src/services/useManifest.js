import { useEffect, useState } from 'react';
import { loadManifest } from './photoService';

// Returns { manifest, error, loading } for the shared photos.json.
export default function useManifest() {
    const [state, setState] = useState({ manifest: null, error: null, loading: true });

    useEffect(() => {
        let active = true;
        loadManifest()
            .then((manifest) => active && setState({ manifest, error: null, loading: false }))
            .catch((error) => {
                console.error('Failed to load photos.json:', error);
                if (active) setState({ manifest: null, error, loading: false });
            });
        return () => { active = false; };
    }, []);

    return state;
}
