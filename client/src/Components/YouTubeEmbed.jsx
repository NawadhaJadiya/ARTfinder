import React from 'react';

const YouTubeEmbed = ({ embedId }) => (
  <div className="relative w-full pt-[56.25%]">
    <iframe
      className="absolute top-0 left-0 right-0 bottom-0 w-full h-full rounded-lg"
      src={`https://www.youtube.com/embed/${embedId}`}
      frameBorder="0"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
      allowFullScreen
      title="Embedded youtube"
    />
  </div>
);

export default YouTubeEmbed; 