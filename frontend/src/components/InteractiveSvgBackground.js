import React, { useEffect, useRef } from 'react';
import './InteractiveSvgBackground.css';

const InteractiveSvgBackground = () => {
  const svgRef = useRef(null);
  const cursorBlobRef = useRef(null);
  const blobsRef = useRef([]);

  useEffect(() => {
    const svg = svgRef.current;
    const cursorBlob = cursorBlobRef.current;
    const blobs = blobsRef.current;
    let animationFrameId;

    const handleMouseMove = (event) => {
      const { clientX, clientY } = event;
      if (cursorBlob) {
        cursorBlob.style.transform = `translate(${clientX}px, ${clientY}px)`;
      }
    };

    window.addEventListener('mousemove', handleMouseMove);

    const moveBlobs = () => {
      const { innerWidth, innerHeight } = window;
      blobs.forEach(blob => {
        const { x, y, vx, vy, r } = blob.dataset;
        let newX = parseFloat(x) + parseFloat(vx);
        let newY = parseFloat(y) + parseFloat(vy);

        if (newX + r > innerWidth || newX - r < 0) blob.dataset.vx *= -1;
        if (newY + r > innerHeight || newY - r < 0) blob.dataset.vy *= -1;

        blob.dataset.x = newX;
        blob.dataset.y = newY;

        blob.style.transform = `translate(${newX}px, ${newY}px)`;
      });

      animationFrameId = requestAnimationFrame(moveBlobs);
    };

    // Initialize blobs
    blobs.forEach(blob => {
      const r = Math.random() * 80 + 40; // radius
      blob.style.width = `${r * 2}px`;
      blob.style.height = `${r * 2}px`;
      blob.dataset.r = r;
      blob.dataset.x = Math.random() * window.innerWidth;
      blob.dataset.y = Math.random() * window.innerHeight;
      blob.dataset.vx = (Math.random() - 0.5) * 2; // velocity x
      blob.dataset.vy = (Math.random() - 0.5) * 2; // velocity y
    });

    animationFrameId = requestAnimationFrame(moveBlobs);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className="svg-background-container">
      <svg ref={svgRef} className="svg-gooey-filter">
        <defs>
          <filter id="gooey">
            <feGaussianBlur in="SourceGraphic" stdDeviation="15" result="blur" />
            <feColorMatrix in="blur" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 25 -10" result="goo" />
            <feComposite in="SourceGraphic" in2="goo" operator="atop" />
          </filter>
        </defs>
      </svg>
      <div className="blobs-container">
        <div ref={cursorBlobRef} className="blob cursor-blob"></div>
        {[...Array(5)].map((_, i) => (
          <div key={i} ref={el => blobsRef.current[i] = el} className="blob"></div>
        ))}
      </div>
    </div>
  );
};

export default InteractiveSvgBackground;
