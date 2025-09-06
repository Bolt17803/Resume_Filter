import { useEffect } from 'react';

/**
 * Custom hook to listen for backend WebSocket notifications for a session.
 * @param {string} sessionId - The session ID to listen for.
 * @param {function} onProcessing - Called when processing starts (optional).
 * @param {function} onDone - Called when processing is done (optional).
 */
export function useSessionWebSocket(sessionId, onProcessing, onDone) {
  useEffect(() => {
    if (!sessionId) return;
    const ws = new window.WebSocket(`ws://localhost:8000/ws/${sessionId}`);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.status === 'processing' && typeof onProcessing === 'function') {
          onProcessing(data.file);
        }
        if (data.status === 'done' && typeof onDone === 'function') {
          onDone(data.file);
        }
      } catch (e) {
        // Ignore parse errors
      }
    };
    return () => ws.close();
  }, [sessionId, onProcessing, onDone]);
}
