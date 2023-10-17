import React from 'react'
import { Link } from 'react-router-dom'
import './TextHeaderWithLine.css'

function TextHeaderWithLine(props) {
    return (
        <>
            <div className='text__header__container'>
                <h3 className='text__header__title'> {props.title} </h3>
                <div className="text__header__gray-box" style={{ width: (props.width || '300px') }} />
            </div>
        </>
    )
}

export default TextHeaderWithLine