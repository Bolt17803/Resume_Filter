import React from 'react';


const Sidebar = ({ sessions, selectedSession, onSessionSelect, onAddSession, onRemoveSession }) => (
  <aside style={{
    width: '220px',
    minHeight: '80vh',
    background: 'rgba(255, 255, 255, 0.10)',
    boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.22), 0 2px 16px 0 rgba(0,0,0,0.10)',
    backdropFilter: 'blur(18px) saturate(160%)',
    WebkitBackdropFilter: 'blur(18px) saturate(160%)',
    borderRadius: '22px',
    border: '1.5px solid rgba(255,255,255,0.35)',
    color: '#3c3535ff',
    padding: '2.2rem 0 1.2rem 0',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    position: 'absolute',
    top: '40px',
    left: '32px',
    zIndex: 10,
    transition: 'box-shadow 0.2s',
  }}>
  <div style={{ display: 'flex', alignItems: 'center', marginBottom: '2rem', width: '85%', justifyContent: 'space-between' }}>
      <h3 style={{ color: '#3c3535ff', margin: 0 }}>Sessions</h3>
      <button
        onClick={onAddSession}
        style={{
          background: '#fff',
          color: '#D9A299',
          border: 'none',
          borderRadius: '50%',
          width: '28px',
          height: '28px',
          fontSize: '1.5rem',
          cursor: 'pointer',
          marginLeft: '8px',
          fontWeight: 'bold',
          boxShadow: '0 1px 3px rgba(0,0,0,0.08)'
        }}
        title="Add Session"
      >
        +
      </button>
    </div>
  <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
      {sessions.map((session) => (
        <div key={session} style={{ width: '90%', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <button
            onClick={() => onSessionSelect(session)}
            style={{
              flex: 1,
              padding: '0.6rem 0.8rem',
              background: session === selectedSession ? 'rgba(250,247,243,0.85)' : 'rgba(240,228,211,0.7)',
              color: '#3c3535ff',
              border: session === selectedSession ? '2px solid #D9A299' : '1px solid #e0cfc2',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: session === selectedSession ? 'bold' : 'normal',
              boxShadow: session === selectedSession ? '0 2px 8px #d9a29922' : '0 1px 3px #0001',
              outline: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'flex-start',
              transition: 'all 0.18s',
            }}
          >
            {session}
          </button>
          <button
            onClick={() => onRemoveSession(session)}
            style={{
              marginLeft: '4px',
              background: 'rgba(255,255,255,0.7)',
              color: '#D9534F',
              border: 'none',
              borderRadius: '50%',
              width: '26px',
              height: '26px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.2rem',
              fontWeight: 'bold',
              boxShadow: '0 1px 3px #0001',
              cursor: 'pointer',
              userSelect: 'none',
              transition: 'background 0.18s',
            }}
            title="Remove Session"
          >
            -
          </button>
        </div>
      ))}
    </div>
  </aside>
);

export default Sidebar;
