import React from 'react'
import { Link } from 'react-router-dom'
import './PhotoCard.css'

function PhotoCard(props) {
    return (
        <>
            <div className='photo__card'>
                <Link className='photo__card__link' to={props.path}>
                    <figure className='photo__card__pic-wrap'>
                        <img src={props.src} className='photo__card__img' />
                    </figure>
                    <h3 className='photo__card__title'> {props.title} </h3>
                </Link>
            </div>
        </>
    )
}

export default PhotoCard