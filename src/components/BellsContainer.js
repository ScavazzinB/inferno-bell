import React, { useState, useEffect, forwardRef, useRef } from 'react';
import Bell from './Bell';
import './BellsContainer.css';

const BellsContainer = forwardRef(({ activeNote }, ref) => {
    const [playingNotes, setPlayingNotes] = useState({});
    const [editMode, setEditMode] = useState(false);
    const [selectedBell, setSelectedBell] = useState(null);

const [bellPositions, setBellPositions] = useState({
    Sol: { top: '86px', left: '310px', width: '64.93333435058594px', height: '79.63333129882812px' },
    Fa: { top: '59px', left: '402px', width: '74.06666564941406px', height: '143.81666564941406px' },
    Mi: { top: '86px', left: '497px', width: '90.06666564941406px', height: '98.96665954589844px' },
    Ré: { top: '81px', left: '593px', width: '93.45001220703125px', height: '118.39999389648438px' },
    Do: { top: '87px', left: '685px', width: '112.59999084472656px', height: '128.60000610351562px' }
});

    const audioRefs = useRef({});
    const dragRef = useRef({ isDragging: false, isResizing: false, handle: null, startX: 0, startY: 0, startWidth: 0, startHeight: 0 });

    useEffect(() => {
        const refs = {};
        Object.keys(bellPositions).forEach((note) => {
            const noteName = note === 'Ré' ? 'ré' : note.toLowerCase();
            refs[note] = new Audio(`${process.env.PUBLIC_URL}/ressource/${noteName}.wav`);
            refs[note].preload = 'auto';
            refs[note].volume = 0.794;
        });
        audioRefs.current = refs;

        return () => {
            Object.values(audioRefs.current).forEach(audio => {
                audio.pause();
                audio.currentTime = 0;
            });
        };
    }, []);

    useEffect(() => {
        if (activeNote) {
            handleBellClick(activeNote);
        }
    }, [activeNote]);

    const handleBellClick = (note, e) => {
        if (editMode) {
            if (e.target.classList.contains('resize-handle')) return;
            setSelectedBell(note);
            return;
        }

        const audio = audioRefs.current[note];
        if (audio) {
            audio.currentTime = 0;
            audio.play().catch(error => {
                console.error('Audio playback error:', error);
            });
        }
        setPlayingNotes(prev => ({ ...prev, [note]: true }));
        setTimeout(() => {
            setPlayingNotes(prev => ({ ...prev, [note]: false }));
        }, 200);
    };

    const handleMouseDown = (e, note) => {
        if (!editMode) return;
        e.preventDefault();

        const target = e.target;
        if (target.classList.contains('resize-handle')) {
            const handle = target.dataset.handle;
            const rect = e.currentTarget.getBoundingClientRect();
            dragRef.current = {
                isDragging: false,
                isResizing: true,
                handle,
                startX: e.clientX,
                startY: e.clientY,
                startWidth: rect.width,
                startHeight: rect.height,
                startLeft: parseInt(bellPositions[note].left),
                startTop: parseInt(bellPositions[note].top)
            };
        } else {
            dragRef.current = {
                isDragging: true,
                isResizing: false,
                startX: e.clientX - parseInt(bellPositions[note].left),
                startY: e.clientY - parseInt(bellPositions[note].top)
            };
        }
        setSelectedBell(note);
    };

    const handleMouseMove = (e) => {
        if (!editMode || !selectedBell) return;
        e.preventDefault();

        if (dragRef.current.isResizing) {
            const { handle, startX, startY, startWidth, startHeight, startLeft, startTop } = dragRef.current;
            const deltaX = e.clientX - startX;
            const deltaY = e.clientY - startY;

            let newWidth = startWidth;
            let newHeight = startHeight;
            let newLeft = startLeft;
            let newTop = startTop;

            if (handle.includes('right')) {
                newWidth = startWidth + deltaX;
            }
            if (handle.includes('left')) {
                newWidth = startWidth - deltaX;
                newLeft = startLeft + deltaX;
            }
            if (handle.includes('bottom')) {
                newHeight = startHeight + deltaY;
            }
            if (handle.includes('top')) {
                newHeight = startHeight - deltaY;
                newTop = startTop + deltaY;
            }

            setBellPositions(prev => ({
                ...prev,
                [selectedBell]: {
                    ...prev[selectedBell],
                    width: `${Math.max(50, newWidth)}px`,
                    height: `${Math.max(50, newHeight)}px`,
                    left: `${newLeft}px`,
                    top: `${newTop}px`
                }
            }));
        } else if (dragRef.current.isDragging) {
            const newLeft = e.clientX - dragRef.current.startX;
            const newTop = e.clientY - dragRef.current.startY;

            setBellPositions(prev => ({
                ...prev,
                [selectedBell]: {
                    ...prev[selectedBell],
                    left: `${newLeft}px`,
                    top: `${newTop}px`
                }
            }));
        }
    };

    const handleMouseUp = () => {
        dragRef.current = { isDragging: false, isResizing: false };
    };

    const handleSavePositions = () => {
        console.log('Bell Positions:', JSON.stringify(bellPositions, null, 2));
    };

    useEffect(() => {
        if (editMode) {
            window.addEventListener('mousemove', handleMouseMove);
            window.addEventListener('mouseup', handleMouseUp);
            return () => {
                window.removeEventListener('mousemove', handleMouseMove);
                window.removeEventListener('mouseup', handleMouseUp);
            };
        }
    }, [editMode, selectedBell]);

    return (
        <div className="bells-container">
            {editMode && (
                <div className="edit-controls">
                    <button onClick={handleSavePositions}>Save Positions</button>
                    {selectedBell && (
                        <div className="position-info">
                            <pre>
                                {selectedBell}: {JSON.stringify(bellPositions[selectedBell], null, 2)}
                            </pre>
                        </div>
                    )}
                </div>
            )}
            <button
                className="edit-toggle"
                onClick={() => setEditMode(!editMode)}
            >
                {editMode ? 'Exit Edit Mode' : 'Enter Edit Mode'}
            </button>
            {Object.entries(bellPositions).map(([note, position]) => (
                <Bell
                    key={note}
                    note={note}
                    isPlaying={playingNotes[note]}
                    onClick={(e) => handleBellClick(note, e)}
                    onMouseDown={(e) => handleMouseDown(e, note)}
                    style={{
                        position: 'absolute',
                        cursor: editMode ? 'move' : 'pointer',
                        border: selectedBell === note ? '2px solid red' : 'none',
                        ...position
                    }}
                    editMode={editMode}
                />
            ))}
        </div>
    );
});

export default BellsContainer;