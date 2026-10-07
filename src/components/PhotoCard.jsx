import React from 'react';
import { Link } from 'react-router-dom';
import { formatAlbumDate } from '../services/photoService';
import './PhotoCard.css';

function PhotoCard({ album }) {
    const cover = album.coverPhoto;
    return (
        <div className="photo__card">
            <Link to={`/photos/${album.slug}`}>
                <figure className="photo__card">
                    {cover && <img src={cover.urls.thumb} alt={cover.alt} loading="lazy" />}
                </figure>
                <h3 className="photo__card__title">{album.title}</h3>
                {album.date && <p className="photo__card__date">{formatAlbumDate(album.date)}</p>}
            </Link>
        </div>
    );
}

export default PhotoCard;
