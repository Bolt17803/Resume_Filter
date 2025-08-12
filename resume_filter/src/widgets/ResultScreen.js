import React, { useState } from 'react';

const ResultScreen = ({ response, sessionId, onQuery }) => {
  const isMulti = Array.isArray(response?.skill_match_score) && Array.isArray(response?.exp_match_score);
  const [minScore, setMinScore] = useState(''); // table filter
  const [query, setQuery] = useState('');       // boolean query
  const [searchMinScore, setSearchMinScore] = useState(''); // min score for backend search
  const [searchResult, setSearchResult] = useState(null);
  const [loading, setLoading] = useState(false);
  let rows = [];

  if (isMulti) {
    const skills = response.skill_match_score;
    const exps = response.exp_match_score;
    const filenames = response.filenames || [];
    const n = Math.max(skills.length, exps.length, filenames.length);

    for (let i = 0; i < n; ++i) {
      const skill = parseFloat(skills[i] ?? 0);
      const exp = parseFloat(exps[i] ?? 0);
      const overall = (0.7 * skill + 0.3 * exp);
      const name = filenames[i] || `Resume ${i + 1}`;
      rows.push({ name, skill, exp, overall });
    }

    rows.sort((a, b) => b.overall - a.overall);
    rows = rows.map((row) => ({ ...row, overall: row.overall.toFixed(2) }));
  }

  const filteredRows = rows.filter(row => minScore === '' || parseFloat(row.overall) >= parseFloat(minScore));

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('query_exp', query);
      formData.append('session_id', sessionId);
      formData.append('score', searchMinScore || '0'); // use separate score value

      const res = await fetch('http://localhost:8000/search/', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      setSearchResult(data);

    } catch (error) {
      console.error('Search error:', error);
      setSearchResult({ error: 'Failed to fetch search results.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'rgba(255, 255, 255, 0.10)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem',
      width: '100%',
    }}>
      <div style={{
        background: '#fff',
        borderRadius: '18px',
        boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.22), 0 2px 16px 0 rgba(0,0,0,0.10)',
        padding: '2.5rem 3.5rem',
        minWidth: '340px',
        textAlign: 'center',
        maxWidth: '90vw'
      }}>
        <h2 style={{ color: '#D9A299', fontWeight: 700, marginBottom: '2rem', fontSize: '2.1rem', letterSpacing: '1px' }}>
          Resume Scan Result
        </h2>

        {response && response.error ? (
          <span style={{ color: 'red', fontSize: '1.2rem' }}>Error: {response.error}</span>
        ) : response ? (
          <>
            <div style={{ fontSize: '1.1rem', color: '#888', marginBottom: '1.5rem' }}>{response.message}</div>
            {response.processing_time !== undefined && (
              <div style={{ fontSize: '1rem', color: '#D9A299', marginBottom: '1.2rem' }}>
                Processing Time: <b>{response.processing_time.toFixed(2)}s</b>
              </div>
            )}

            {isMulti ? (
              <>
                {/* Table filter input */}
                <div style={{ marginBottom: '1rem', textAlign: 'left' }}>
                  <label style={{ color: '#3c3535ff', fontWeight: 600, fontSize: '1rem' }}>
                    Show only results with overall score ≥{' '}
                    <input
                      type="number"
                      min={0}
                      max={100}
                      step={0.01}
                      value={minScore}
                      onChange={e => setMinScore(e.target.value)}
                      style={{
                        width: '70px',
                        marginLeft: '0.5rem',
                        borderRadius: '5px',
                        border: '1px solid #D9A299',
                        padding: '0.2rem 0.5rem'
                      }}
                    />
                  </label>
                </div>

                {/* Results table */}
                <div style={{ overflowX: 'auto', maxHeight: '60vh' }}>
                  <table style={{
                    borderCollapse: 'collapse',
                    width: '100%',
                    minWidth: '350px',
                    background: '#FAF7F3',
                    borderRadius: '8px',
                    boxShadow: '0 1px 6px #0001'
                  }}>
                    <thead>
                      <tr style={{ background: '#D9A299', color: '#fff', fontWeight: 600, position: 'sticky', top: 0, zIndex: 1 }}>
                        <th style={{ padding: '0.7rem 1.2rem', borderRadius: '8px 0 0 0' }}>Resume File</th>
                        <th style={{ padding: '0.7rem 1.2rem' }}>Skill Match (%)</th>
                        <th style={{ padding: '0.7rem 1.2rem' }}>Experience Match (%)</th>
                        <th style={{ padding: '0.7rem 1.2rem' }}> Overall Score </th>
                        <th style={{ padding: '0.7rem 1.2rem', borderRadius: '0 8px 0 0' }}>Query</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredRows.map((row, i) => (
                        <tr key={row.name || i} style={{ background: i % 2 === 0 ? '#F0E4D3' : '#fff' }}>
                          <td style={{ padding: '0.6rem 1.2rem', fontWeight: 500 }}>{row.name}</td>
                          <td style={{ padding: '0.6rem 1.2rem', color: '#4caf50', fontWeight: 600 }}>{row.skill}</td>
                          <td style={{ padding: '0.6rem 1.2rem', color: '#2196f3', fontWeight: 600 }}>{row.exp}</td>
                          <td style={{ padding: '0.6rem 1.2rem', color: '#D9A299', fontWeight: 700 }}>{row.overall}</td>
                          <td style={{ padding: '0.6rem 1.2rem' }}>
                            <button
                              style={{ background: '#D9A299', color: '#fff', border: 'none', borderRadius: '6px', padding: '0.4rem 1.2rem', cursor: 'pointer' }}
                              onClick={() => onQuery && onQuery(row.name)}
                            >
                              Query
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            ) : (
              <div> {/* single result cards here if needed */} </div>
            )}

            {/* Boolean Search Section */}
            <div style={{ marginTop: '2rem', textAlign: 'left' }}>
              <h3 style={{ color: '#3c3535ff', fontWeight: 600 }}>Boolean Search</h3>

              {/* Boolean query input */}
              <input
                type="text"
                placeholder="Enter boolean query..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                style={{
                  width: '50%',
                  padding: '0.5rem',
                  marginRight: '0.5rem',
                  borderRadius: '5px',
                  border: '1px solid #D9A299'
                }}
              />

              {/* Min score for backend search */}
              <input
                type="number"
                placeholder="Min score"
                min={0}
                max={100}
                step={0.01}
                value={searchMinScore}
                onChange={(e) => setSearchMinScore(e.target.value)}
                style={{
                  width: '20%',
                  padding: '0.5rem',
                  marginRight: '0.5rem',
                  borderRadius: '5px',
                  border: '1px solid #D9A299'
                }}
              />

              <button
                onClick={handleSearch}
                disabled={loading}
                style={{
                  background: '#D9A299',
                  color: '#fff',
                  padding: '0.5rem 1rem',
                  borderRadius: '5px',
                  border: 'none',
                  cursor: 'pointer'
                }}
              >
                {loading ? 'Searching...' : 'Search'}
              </button>

              {searchResult && (
                <div style={{ marginTop: '1rem', background: '#F0E4D3', padding: '1rem', borderRadius: '8px' }}>
                  <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(searchResult, null, 2)}</pre>
                </div>
              )}
            </div>
          </>
        ) : (
          <span>No response data.</span>
        )}
      </div>
    </div>
  );
};

export default ResultScreen;
