import React, { useState } from 'react';

const CollapsiblePanel = ({ title, content }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="collapsible-panel">
      <div className="collapsible-header" onClick={() => setIsExpanded(!isExpanded)}>
        {title} {isExpanded ? '▲' : '▼'}
      </div>
      {isExpanded && <div className="collapsible-content">{content}</div>}
    </div>
  );
};

export default CollapsiblePanel;
