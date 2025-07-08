import React from 'react';
import { getAssetUrl, getStreamUrl } from '../api/session';

function DashboardObject({ object }) {
  return (
    <div className="object-card-outer">
      <div className="object-card" data-object-id={object.id}>
        <div className="object-header">
          <span className="object-icon">{object.icon || ''}</span>
          <span className="object-type">{object.type}</span>
        </div>
        <div className="object-status">
          <div className="object-id">{object.id}</div>
          <div className="object-asset-links">
            <a href={getAssetUrl(object.id, 'default')} target="_blank" rel="noopener noreferrer">View Default Asset</a>
            <a href={getAssetUrl(object.id, 'widget')} target="_blank" rel="noopener noreferrer">View Widget Asset</a><br />
            <a href={getStreamUrl(object.id, 'default')} target="_blank" rel="noopener noreferrer">🎥 Live Default Stream</a>
            <a href={getStreamUrl(object.id, 'widget')} target="_blank" rel="noopener noreferrer">🎥 Live Widget Stream</a>
          </div>
        </div>
        {object.fields && (
          <div className="object-fields">
            <ul>
              {Object.entries(object.fields).map(([key, value]) => (
                <li key={key}><b>{key}</b>: {String(value)}</li>
              ))}
            </ul>
          </div>
        )}
        {object.render_data && (
          <div className="object-render-data">
            <pre>{JSON.stringify(object.render_data, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default DashboardObject;
