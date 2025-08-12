import React from 'react';

const Loading = ({ text = "Processing, please wait..." }) => (
  <div style={{
    position: 'absolute', top: 0, left: 0, width: '100vw', height: '100vh',
    background: 'rgba(255,255,255,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
  }}>
    <div style={{
      padding: '2rem 3rem', background: '#fff', borderRadius: '12px', boxShadow: '0 2px 12px #0002',
      display: 'flex', flexDirection: 'column', alignItems: 'center'
    }}>
      <div className="loader" style={{
        border: '4px solid #f3f3f3', borderTop: '4px solid #D9A299', borderRadius: '50%',
        width: '40px', height: '40px', animation: 'spin 1s linear infinite', marginBottom: '1rem'
      }} />
      <span style={{ color: '#3c3535ff', fontWeight: 500 }}>{text}</span>
      <style>
        {`@keyframes spin { 0% { transform: rotate(0deg);} 100% { transform: rotate(360deg);} }`}
      </style>
    </div>
  </div>
);

export default Loading;
