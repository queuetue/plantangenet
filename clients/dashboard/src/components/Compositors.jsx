import React from 'react';

function Compositors({ compositors }) {
  const compsArr = Object.values(compositors || {});
  if (compsArr.length === 0) {
    return <div className="empty-state">No compositors found</div>;
  }
  return (
    <div className="compositors-grid">
      {compsArr.map(comp => (
        <div key={comp.id} className={`compositor-card ${comp.active ? 'active' : 'inactive'}`}>
          <span className="compositor-name">{comp.id}</span>
          <span className="compositor-type">{comp.type}</span>
          <span className="compositor-status">{comp.active ? '🟢' : '🔴'}</span>
        </div>
      ))}
    </div>
  );
}

export default Compositors;
