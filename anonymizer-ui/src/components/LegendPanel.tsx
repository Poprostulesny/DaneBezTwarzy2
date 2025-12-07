import React from 'react';
import { labelColors } from '../services/mockAnonymizer';

export const LegendPanel: React.FC = () => {
  return (
    <div className="legend-panel">
      <h4>Entity Types</h4>
      <div className="legend-items">
        {Object.entries(labelColors).map(([label, color]) => (
          <div key={label} className="legend-item">
            <span
              className="legend-color"
              style={{
                backgroundColor: `${color}22`,
                border: `2px solid ${color}`,
              }}
            ></span>
            <span className="legend-label">{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
