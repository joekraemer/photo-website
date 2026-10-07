import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { formatAlbumDate } from '../services/photoService';
import './PhotoCard.css';

function PhotoCard({ album }) {
    const cover = album.coverPhoto;
    const navigate = useNavigate();
    const to = `/photos/${album.slug}`;

    // Links open on Enter already; let Space open the album too, like a button.
    const onKeyDown = (event) => {
        if (event.key === ' ') {
            event.preventDefault();
            navigate(to);
        }
    };

    return (
        <div className="photo__card">
            <Link to={to} onKeyDown={onKeyDown}>
                <figure className="photo__card">
                    {cover && (
                        <img
                            src={cover.urls.thumb}
                            alt={cover.alt}
                            width={cover.width}
                            height={cover.height}
                            loading="lazy"
                            decoding="async"
                        />
                    )}
                </figure>
                <h3 className="photo__card__title">{album.title}</h3>
                {album.date && <p className="photo__card__date">{formatAlbumDate(album.date)}</p>}
            </Link>
        </div>
    );
}

export default PhotoCard;
