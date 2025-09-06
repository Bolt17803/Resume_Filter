
import Loading from './Loading';

const MainScreen = ({
  file,
  handleFileChange,
  jobDescriptionFile,
  handleJobDescriptionFileChange,
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
      

      {/* File Upload Card */}
      <form onSubmit={handleSubmit} style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '2.5rem',
        background: 'rgba(255,255,255,0.7)',
        borderRadius: '18px',
        boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.22), 0 2px 16px 0 rgba(0,0,0,0.10)',
        padding: '2.5rem 2.5rem',
        minWidth: '520px',
        maxWidth: '95vw',
        marginBottom: '1rem',
      }}>
        {/* Upload Options Row */}
        <div style={{
          display: 'flex',
          flexDirection: 'row',
          alignItems: 'center',
          gap: '2.5rem',
          width: '100%',
        }}>
          {/* Job Description Upload */}
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
            <label htmlFor="job-description-input" style={{ color: '#3c3535ff', fontWeight: 600, fontSize: '1.1rem', marginBottom: '0.5rem' }}>
              Job Description (PDF):
            </label>
            <input
              id="job-description-input"
              type="file"
              accept=".pdf"
              onChange={handleJobDescriptionFileChange}
              style={{
                display: 'none',
              }}
            />
            <label htmlFor="job-description-input" style={{
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
              {jobDescriptionFile && jobDescriptionFile.name ? `Selected: ${jobDescriptionFile.name}` : 'Click to select job description'}
            </label>
            <div style={{ flex: 1 }} />
          </div>

          {/* Resume File Upload */}
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
              Resume File (PDF or ZIP):
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
              {file && file.name ? `Selected: ${file.name}` : 'Click to select resume file'}
            </label>
            <div style={{ flex: 1 }} />
          </div>
        </div>

        {/* Submit Button */}
        <button type="submit" style={{
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
