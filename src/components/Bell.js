import React from 'react';
import './Bell.css';

const Bell = ({ note, isPlaying, onClick, onMouseDown, style, editMode }) => {
    return (
        <div
            className={`bell ${note.toLowerCase()} ${isPlaying ? 'playing' : ''}`}
            onClick={onClick}
            onMouseDown={onMouseDown}
            style={style}
        >
            {editMode && (
                <>
                    <div className="resize-handle top-left" data-handle="top-left" />
                    <div className="resize-handle top-right" data-handle="top-right" />
                    <div className="resize-handle bottom-left" data-handle="bottom-left" />
                    <div className="resize-handle bottom-right" data-handle="bottom-right" />
                </>
            )}
        </div>
    );
};

export default Bell;