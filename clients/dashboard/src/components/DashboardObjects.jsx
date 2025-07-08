import React from 'react';
import DashboardObject from './DashboardObject';

function DashboardObjects({ objects }) {
  if (!objects || objects.length === 0) {
    return (
      <div className="empty-state">
        No dashboard objects found
      </div>
    );
  }

  return (
    <div className="objects-grid">
      {objects.map(obj => (
        <DashboardObject key={obj.id} object={obj} />
      ))}
    </div>
  );
}

export default DashboardObjects;
