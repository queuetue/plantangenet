import React from 'react';

function CurrentActivity({ activity }) {
  if (!activity) return null;
  return (
    <div className="activity-panel">
      <h3>Current Activity: {activity.game_id || 'Unknown'}</h3>
      <div className="game-info">
        <div>State: {activity.state || 'Unknown'}</div>
        <div>Turn: {activity.current_turn || 'None'}</div>
        <div>Frames: {activity.frames_elapsed || 0}</div>
        <div>Score: {(activity.board && activity.board.score) || 0}</div>
        <div>Lives: {(activity.board && activity.board.lives) || 0}</div>
      </div>
    </div>
  );
}

export default CurrentActivity;
