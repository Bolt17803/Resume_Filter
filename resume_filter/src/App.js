import React, { useState, useRef } from 'react';
import './App.css';
import Sidebar from './widgets/Sidebar';
import MainScreen from './widgets/MainScreen';
import Loading from './widgets/Loading';
import ResultScreen from './widgets/ResultScreen';
import QueryScreen from './widgets/QueryScreen';

function App() {
  const [skillsInput, setSkillsInput] = useState('');
  const [experienceInput, setExperienceInput] = useState('');
  const [file, setFile] = useState(null);
  const [sessionCount, setSessionCount] = useState(1);
  const [response, setResponse] = useState(null);
  const [sessions, setSessions] = useState(['session-1']);
  const [selectedSession, setSelectedSession] = useState('session-1');
  const [loading, setLoading] = useState(false);
  const sessionIdRef = useRef(1);
  const [page, setPage] = useState('main'); // 'main' or 'result'
  const [resultSession, setResultSession] = useState(null); // session for which to show result
  const [resultData, setResultData] = useState(null); // result data fetched from backend
  const [pageQuery, setPageQuery] = useState(null); // { fileName: string }

  const handleSkillsChange = (e) => {
    setSkillsInput(e.target.value);
  };

  const handleExperienceChange = (e) => {
    setExperienceInput(e.target.value);
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file || !skillsInput || !experienceInput) {
      alert('Please enter skills, experience, and select a file.');
      return;
    }
    const sessionId = selectedSession;
    const formData = new FormData();
    formData.append('file', file);
    formData.append('skills_input', skillsInput);
    formData.append('experience_input', experienceInput);
    formData.append('session_id', sessionId);

    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/upload/', {
        method: 'POST',
        body: formData,
      });
      
      // Check if the response is OK (status code 2xx)
      if (!res.ok) {
        throw new Error(`HTTP error! Status: ${res.status} ${res.statusText}`);
      }

      const data = await res.json(); // Parse the response
      console.log('Backend response:', data); // Log the response for debugging

      // Check if the response contains an error
      if (data.error) {
        throw new Error(data.error);
      }

      setSkillsInput('');
      setExperienceInput('');
      setFile(null);
      document.getElementById('file-input').value = '';
      setResultSession(sessionId);
      setPage('result');
    } catch (err) {
      console.error('Upload error:', err.message); // Log the error for debugging
      setResponse({ error: `Upload failed: ${err.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleAddSession = () => {
    sessionIdRef.current += 1;
    setSessionCount(sessionIdRef.current);
    const newSession = `session-${sessionIdRef.current}`;
    setSessions((prev) => [...prev, newSession]);
    setSelectedSession(newSession);
    setResponse(null);
  };

  const handleSessionSelect = async (session) => {
    setSelectedSession(session);
    setResponse(null);
    // Check if result exists for this session
    try {
      const res = await fetch(`http://localhost:8000/session_result/${session}`);
      if (res.ok) {
        setResultSession(session);
        setPage('result');
      } else {
        setPage('main');
      }
    } catch {
      setPage('main');
    }
  };

  const handleRemoveSession = (session) => {
    // Prevent removing the last session
    if (sessions.length === 1) return;
    const idx = sessions.indexOf(session);
    const newSessions = sessions.filter((s) => s !== session);
    setSessions(newSessions);
    // If the removed session was selected, select the previous or next session
    if (selectedSession === session) {
      const newIdx = idx > 0 ? idx - 1 : 0;
      setSelectedSession(newSessions[newIdx]);
    }
  };

  // Fetch result data from backend when resultSession or page changes
  React.useEffect(() => {
    const fetchResult = async () => {
      if (page === 'result' && resultSession) {
        try {
          const res = await fetch(`http://localhost:8000/session_result/${resultSession}`);
          const data = await res.json();
          setResultData(data);
        } catch (e) {
          setResultData({ error: 'Could not fetch result.' });
        }
      }
    };
    fetchResult();
  }, [page, resultSession]);

  return (
    <>
      {loading && <Loading text="Uploading and processing, please wait..." />}
      <div className="App" style={{ display: 'flex', height: '100vh' }}>
        <Sidebar
          sessions={sessions}
          selectedSession={selectedSession}
          onSessionSelect={handleSessionSelect}
          onAddSession={handleAddSession}
          onRemoveSession={handleRemoveSession}
        />
        {pageQuery ? (
          <QueryScreen
            fileName={pageQuery.fileName}
            sessionId={resultSession}
            onBack={() => setPageQuery(null)}
          />
        ) : page === 'main' ? (
          <MainScreen
            skillsInput={skillsInput}
            handleSkillsChange={handleSkillsChange}
            experienceInput={experienceInput}
            handleExperienceChange={handleExperienceChange}
            file={file}
            handleFileChange={handleFileChange}
            handleSubmit={handleSubmit}
            selectedSession={selectedSession}
            response={response}
          />
        ) : (
          <ResultScreen
            response={resultData}
            sessionId={resultSession}
            onQuery={fileName => setPageQuery({ fileName })}
          />
        )}
      </div>
    </>
  );
}

export default App;