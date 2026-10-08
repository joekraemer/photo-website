import React from 'react';
import { Link, useNavigate } from 'react-router';
import { formatAlbumDate, placeholderProps } from '../services/photoService';
import './PhotoCard.css';

// The card slot is 100vw on phones, 300px on tablets and 226px on desktop
// (see PhotosPage.css). A cover wider than 2:3 is cropped, so it renders wider
// than its slot by 1.5 * its aspect ratio; scale the hint so the browser picks
// a size that stays sharp after the crop.
function coverSizes(cover) {
    const aspect = cover.width && cover.height ? cover.width / cover.height : 2 / 3;
    const crop = Math.max(1, 1.5 * aspect);
    const px = (n) => `${Math.round(n * crop)}px`;
    return `(max-width: 730px) ${Math.round(100 * crop)}vw, (max-width: 960px) ${px(300)}, ${px(226)}`;
}

function PhotoCard({ album }) {
    const cover = album.coverPhoto;
    const navigate = useNavigate();
    const to = `/photos/${album.slug}`;
    const label = album.date ? `${album.title}, ${formatAlbumDate(album.date)}` : album.title;

    // Links open on Enter already; let Space open the album too, like a button.
    const onKeyDown = (event) => {
        if (event.key === ' ') {
            event.preventDefault();
            navigate(to);
        }
    };

    return (
        <div className="photo__card">
            <Link to={to} onKeyDown={onKeyDown} aria-label={label}>
                <figure className="photo__card">
                    {cover && (
                        <img
                            src={cover.urls.thumb}
                            srcSet={`${cover.urls.thumb} 500w, ${cover.urls.medium} 1600w`}
                            sizes={coverSizes(cover)}
                            alt=""
                            width={cover.width}
                            height={cover.height}
                            loading="lazy"
                            decoding="async"
                            {...placeholderProps(cover)}
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
