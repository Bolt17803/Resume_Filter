
import Loading from './Loading';



const MainScreen = ({
  skillsInput,
  handleSkillsChange,
  experienceInput,
  handleExperienceChange,
  file,
  handleFileChange,
  handleSubmit,
  selectedSession,
  response,
  loading
}) => (
  <div style={{
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'rgba(255, 255, 255, 0.10)',
    minHeight: '100vh',
    width: '100%',
    position: 'relative',
  }}>
    {loading && <Loading text="Uploading and processing, please wait..." />}
    <header className="App-header" style={{ background: 'none', boxShadow: 'none' }}>
      <h2 style={{ color: '#3c3535ff', marginBottom: '2.5rem' }}>Resume Filter Upload</h2>
      <form onSubmit={handleSubmit} style={{
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'flex-start',
        gap: '2.5rem',
        background: 'rgba(255,255,255,0.7)',
        borderRadius: '18px',
        boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.22), 0 2px 16px 0 rgba(0,0,0,0.10)',//'0 2px 18px #d9a2998d',
        padding: '2.5rem 2.5rem',
        minWidth: '520px',
        maxWidth: '95vw',
      }}>
        {/* Column 1: Skills & Experience */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem', minWidth: '260px', flex: 1 }}>
          <label style={{ color: '#3c3535ff', width: '100%', fontWeight: 600 }}>
            Skills (point-wise):
            <textarea
              value={skillsInput}
              onChange={handleSkillsChange}
              style={{ width: '100%', minHeight: '60px', resize: 'vertical', borderRadius: '8px', border: '1.5px solid #D9A299', padding: '0.7rem', marginTop: '0.4rem', fontSize: '1rem' }}
              placeholder="e.g.\n- Python\n- React\n- FastAPI"
              required
            />
          </label>
          <label style={{ color: '#3c3535ff', width: '100%', fontWeight: 600 }}>
            Experience (point-wise):
            <textarea
              value={experienceInput}
              onChange={handleExperienceChange}
              style={{ width: '100%', minHeight: '60px', resize: 'vertical', borderRadius: '8px', border: '1.5px solid #D9A299', padding: '0.7rem', marginTop: '0.4rem', fontSize: '1rem' }}
              placeholder="e.g.\n- 3 years at Company X\n- Built Y system"
              required
            />
          </label>
        </div>
        {/* Column 2: File Uploader */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1.2rem',
          minWidth: '220px',
          maxWidth: '270px',
          flex: 1,
          background: 'linear-gradient(135deg, #FAF7F3 60%, #D9A299 100%)',
          borderRadius: '14px',
          boxShadow: '0 2px 18px #d9a2998d',
          padding: '1.5rem 1.2rem',
          height: '100%',
          boxSizing: 'border-box',
        }}>
          <div style={{ flex: 1 }} />
          <label htmlFor="file-input" style={{ color: '#3c3535ff', fontWeight: 600, fontSize: '1.1rem', marginBottom: '0.5rem' }}>
            Upload file (PDF or ZIP):
          </label>
          <input
            id="file-input"
            type="file"
            accept=".pdf,.zip"
            onChange={handleFileChange}
            required
            style={{
              display: 'none',
            }}
          />
          <label htmlFor="file-input" style={{
            display: 'inline-block',
            background: '#fff',
            color: '#D9A299',
            border: '2px dashed #D9A299',
            borderRadius: '8px',
            padding: '1.1rem 2.2rem',
            fontWeight: 700,
            fontSize: '1.1rem',
            cursor: 'pointer',
            boxShadow: '0 1px 6px #0001',
            transition: 'background 0.18s, color 0.18s',
          }}>
            {file && file.name ? `Selected: ${file.name}` : 'Click to select file'}
          </label>
          <button type="submit" style={{
            marginTop: '1.2rem',
            background: '#D9A299',
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            padding: '0.7rem 2.2rem',
            fontWeight: 700,
            fontSize: '1.1rem',
            cursor: 'pointer',
            boxShadow: '0 1px 6px #0001',
            transition: 'background 0.18s',
          }}>Submit</button>
          <div style={{ flex: 1 }} />
        </div>
      </form>
      {response && (
        <div style={{ marginTop: '1rem' }}>
          {response.error ? (
            <span style={{ color: 'red' }}>Error: {response.error}</span>
          ) : (
            <span style={{ color: 'lightgreen' }}>Success! Uploaded {response.filename} (Session: {response.session_id})</span>
          )}
        </div>
      )}
    </header>
  </div>
);

export default MainScreen;
