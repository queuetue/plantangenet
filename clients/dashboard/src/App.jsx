import React, { useState, useEffect } from 'react';
import DashboardObjects from './components/DashboardObjects';
import Compositors from './components/Compositors';
import CurrentActivity from './components/CurrentActivity';
import RefreshStatus from './components/RefreshStatus';
import { fetchSessionData } from './api/session';

function App() {
  const [sessionData, setSessionData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshStatus, setRefreshStatus] = useState('🟡 Loading...');

  const updateData = async () => {
    try {
      setRefreshStatus('🔄 Fetching...');
      const data = await fetchSessionData();
      
      // Validate data structure
      if (!Array.isArray(data.dashboard_objects)) {
        throw new Error('dashboard_objects must be an array');
      }
      
      setSessionData(data);
      setError(null);
      setRefreshStatus('🟢 Live');
    } catch (err) {
      console.error('Failed to fetch session data:', err);
      setError(err.message);
      setRefreshStatus('🔴 Error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial load
    updateData();

    // Set up polling every 2 seconds
    const interval = setInterval(updateData, 2000);

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="dashboard">
        <div className="loading-spinner">
          <h2>🌿 Loading Plantangenet Dashboard...</h2>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard">
        <div className="error-message">
          <h2>❌ Dashboard Error</h2>
          <p>{error}</p>
          <button onClick={updateData} style={{ marginTop: '10px', padding: '8px 16px' }}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <RefreshStatus status={refreshStatus} />
      
      <div className="header">
        <h1>🌿 Plantangenet Session Dashboard</h1>
        <div className="session-id">
          Session: {sessionData?.session_id || 'Unknown'}
        </div>
      </div>

      <div className="panel">
        <h2>🧩 Objects ({sessionData?.dashboard_objects?.length || 0})</h2>
        <DashboardObjects objects={sessionData?.dashboard_objects || []} />
      </div>

      <div className="panel">
        <h2>🎥 Compositors ({Object.keys(sessionData?.compositors || {}).length})</h2>
        <Compositors compositors={sessionData?.compositors || {}} />
      </div>

    <div className="panel">
        <h2>🤖 Agents ({Object.keys(sessionData?.agents || {}).length})</h2>
        <ul>
        {Object.values(sessionData?.agents || {}).map(agent => (
        <li key={agent.id}>
            <pre>{JSON.stringify(agent, null, 2)}</pre>
        </li>
        ))}
        </ul>
    </div>

      {sessionData?.current_activity && (
        <div className="panel">
          <h2>🎮 Current Activity</h2>
          <CurrentActivity activity={sessionData.current_activity} />
        </div>
      )}

      {/* Render additional groups dynamically */}
      {sessionData && Object.entries(sessionData)
        .filter(([key, value]) => {
          // Exclude already-handled keys
          return ![
            'session_id',
            'dashboard_objects',
            'compositors',
            'current_activity',
            'activities',
            'agents',
          ].includes(key) && value && (Array.isArray(value) || (typeof value === 'object' && Object.keys(value).length > 0));
        })
        .map(([key, value]) => (
          <div className="panel" key={key}>
            <h2>{key.charAt(0).toUpperCase() + key.slice(1)} ({Array.isArray(value) ? value.length : Object.keys(value).length})</h2>
            <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
              {Array.isArray(value)
                ? value.map((item, idx) => (
                    <li key={item.id || idx} style={{ marginBottom: 8 }}>
                      <pre style={{ margin: 0 }}>{JSON.stringify(item, null, 2)}</pre>
                    </li>
                  ))
                : Object.entries(value).map(([id, item]) => (
                    <li key={id} style={{ marginBottom: 8 }}>
                      <pre style={{ margin: 0 }}>{JSON.stringify(item, null, 2)}</pre>
                    </li>
                  ))}
            </ul>
          </div>
        ))}
      {/* End dynamic groups */}
    </div>
  );
}

export default App;
