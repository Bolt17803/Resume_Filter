import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';

const QueryScreen = ({ fileName, sessionId, onBack }) => {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setAnswer('');
    try {
      const res = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_name: fileName, sessionId: sessionId, question: question }),
      });
      const data = await res.json();
      setAnswer(data.answer);
    } catch (err) {
      setAnswer('Error fetching answer.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        width: '100%',
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(255, 255, 255, 0.10)',
        position: 'relative',
      }}
    >
      <div
        style={{
          background: '#fff',
          borderRadius: '18px',
          boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.22), 0 2px 16px 0 rgba(0,0,0,0.10)',
          padding: '2.5rem 3.5rem',
          minWidth: '340px',
          textAlign: 'center',
          maxWidth: '90vw', // Keep responsive
          marginLeft: '60px',
          marginRight: '60px',
          position: 'relative',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          boxSizing: 'border-box', // Prevent padding issues
        }}
      >
        <button
          onClick={onBack}
          style={{
            position: 'absolute',
            left: 24,
            top: 24,
            background: '#D9A299',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            padding: '0.4rem 1.2rem',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: '1rem',
            boxShadow: '0 1px 6px #0001',
          }}
        >
          Back
        </button>
        <h2
          style={{
            color: '#D9A299',
            fontWeight: 700,
            marginBottom: '2rem',
            fontSize: '2.1rem',
            letterSpacing: '1px',
          }}
        >
          Query Resume: {fileName}
        </h2>
        <form
          onSubmit={handleSubmit}
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '1.2rem',
            alignItems: 'center',
            width: '100%',
          }}
        >
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about this resume..."
            style={{
              width: '100%',
              minWidth: '260px',
              maxWidth: '600px', // Increased for better usability
              minHeight: '60px',
              borderRadius: '8px',
              border: '1.5px solid #D9A299',
              padding: '0.7rem',
              fontSize: '1rem',
              boxSizing: 'border-box',
            }}
            required
          />
          <button
            type="submit"
            style={{
              background: '#D9A299',
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              padding: '0.7rem 2.2rem',
              fontWeight: 700,
              fontSize: '1.1rem',
              cursor: 'pointer',
              boxShadow: '0 1px 6px #0001',
              marginTop: '0.5rem',
            }}
            disabled={loading}
          >
            {loading ? 'Processing...' : 'Ask'}
          </button>
        </form>
        {answer && (
          <div
            style={{
              marginTop: '2rem',
              color: '#3c3535ff',
              fontWeight: 500, // Slightly lighter for readability
              fontSize: '0.95rem', // Reduced font size
              background: '#F0E4D3',
              borderRadius: '10px',
              padding: '1.2rem 2.2rem',
              boxShadow: '0 1px 6px #0001',
              width: '100%',
              maxWidth: '600px', // Increased to accommodate content
              boxSizing: 'border-box',
              overflowWrap: 'break-word', // Ensure long words wrap
              wordBreak: 'break-word', // Handle very long strings
              maxHeight: '400px', // Limit height to prevent excessive growth
              overflowY: 'auto', // Add scroll for long content
            }}
          >
            <ReactMarkdown
              components={{
                // Customize markdown rendering
                p: ({ children }) => <p style={{ margin: '0.5rem 0', lineHeight: '1.5' }}>{children}</p>,
                ul: ({ children }) => <ul style={{ marginLeft: '1.5rem', listStyleType: 'disc' }}>{children}</ul>,
                li: ({ children }) => <li style={{ marginBottom: '0.5rem' }}>{children}</li>,
                strong: ({ children }) => <strong style={{ fontWeight: 700 }}>{children}</strong>,
              }}
            >
              {answer}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
};

export default QueryScreen; 