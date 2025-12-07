import React from 'react';
import { labelColors } from '../services/mockAnonymizer';

interface TextPanelProps {
  title: string;
  text: string;
  highlightLabels?: boolean;
  icon?: React.ReactNode;
}

export const TextPanel: React.FC<TextPanelProps> = ({ title, text, highlightLabels = false, icon }) => {
  const renderHighlightedText = (content: string) => {
    if (!highlightLabels) {
      return <span>{content}</span>;
    }

    // Find all $[LABEL] patterns and highlight them (including labels with hyphens like DATE-OF-BIRTH)
    const regex = /\$\[([A-Z\-]+)\]/g;
    const parts: React.ReactNode[] = [];
    let lastIndex = 0;
    let match;

    while ((match = regex.exec(content)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        parts.push(
          <span key={`text-${lastIndex}`}>
            {content.substring(lastIndex, match.index)}
          </span>
        );
      }

      // Add the highlighted label
      const label = match[1];
      const color = labelColors[label] || '#888';
      parts.push(
        <span
          key={`label-${match.index}`}
          className="label-tag"
          style={{
            backgroundColor: `${color}22`,
            color: color,
            border: `1px solid ${color}`,
            padding: '2px 8px',
            borderRadius: '4px',
            fontWeight: 600,
            fontSize: '0.9em',
          }}
        >
          ${`[${label}]`}
        </span>
      );

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < content.length) {
      parts.push(
        <span key={`text-${lastIndex}`}>
          {content.substring(lastIndex)}
        </span>
      );
    }

    return <>{parts}</>;
  };

  return (
    <div className="text-panel">
      <div className="panel-header">
        {icon && <span className="panel-icon">{icon}</span>}
        <h3>{title}</h3>
      </div>
      <div className="panel-content">
        {text ? (
          <pre className="text-content">{renderHighlightedText(text)}</pre>
        ) : (
          <div className="empty-state">
            <span className="empty-icon">📄</span>
            <p>No text to display</p>
          </div>
        )}
      </div>
    </div>
  );
};
