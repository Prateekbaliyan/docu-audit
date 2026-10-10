import { useState, useCallback, useRef, useEffect } from "react";

export interface TransformState {
  scale: number;
  x: number;
  y: number;
}

export function useSynchronizedZoomPan(initialScale = 1) {
  const [transform, setTransform] = useState<TransformState>({
    scale: initialScale,
    x: 0,
    y: 0,
  });

  const isDragging = useRef(false);
  const startPos = useRef({ x: 0, y: 0 });

  const zoomIn = useCallback(() => {
    setTransform((prev) => ({
      ...prev,
      scale: Math.min(prev.scale * 1.2, 5.0),
    }));
  }, []);

  const zoomOut = useCallback(() => {
    setTransform((prev) => ({
      ...prev,
      scale: Math.max(prev.scale / 1.2, 0.5),
    }));
  }, []);

  const resetZoom = useCallback(() => {
    setTransform({ scale: 1, x: 0, y: 0 });
  }, []);

  const handleWheel = useCallback((e: WheelEvent) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    setTransform((prev) => {
      const newScale = Math.min(Math.max(prev.scale * zoomFactor, 0.5), 5.0);
      return {
        ...prev,
        scale: newScale,
      };
    });
  }, []);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    isDragging.current = true;
    startPos.current = { x: e.clientX - transform.x, y: e.clientY - transform.y };
  }, [transform]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDragging.current) return;
    setTransform((prev) => ({
      ...prev,
      x: e.clientX - startPos.current.x,
      y: e.clientY - startPos.current.y,
    }));
  }, []);

  const handleMouseUp = useCallback(() => {
    isDragging.current = false;
  }, []);

  return {
    transform,
    setTransform,
    zoomIn,
    zoomOut,
    resetZoom,
    bindContainer: {
      onMouseDown: handleMouseDown,
      onMouseMove: handleMouseMove,
      onMouseUp: handleMouseUp,
      onMouseLeave: handleMouseUp,
    },
    handleWheel,
  };
}
