// src/components/CameraFeed.js
import React, {
  useRef,
  useEffect,
  useState,
  forwardRef,
  useImperativeHandle
} from 'react';
import { Box } from '@chakra-ui/react';

const CameraFeed = forwardRef(({ onCaptureFrame }, ref) => {
  const videoRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [facingMode, setFacingMode] = useState('user');
  const [isPortrait, setIsPortrait] = useState(window.innerHeight > window.innerWidth);

  const updateOrientation = () => setIsPortrait(window.innerHeight > window.innerWidth);

  useEffect(() => {
    window.addEventListener('resize', updateOrientation);
    updateOrientation();
    return () => window.removeEventListener('resize', updateOrientation);
  }, []);

  useEffect(() => {
    let localStream;
    const initCamera = async () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
      try {
        const newStream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode }
        });
        setStream(newStream);
        if (videoRef.current) {
          videoRef.current.srcObject = newStream;
        }
      } catch (err) {
        console.error(`Error accessing camera with facingMode="${facingMode}":`, err);
      }
    };
    initCamera();
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [facingMode]);

  const captureFrame = () => {
    if (!videoRef.current) return;
    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataURL = canvas.toDataURL('image/jpeg');
    const base64Data = dataURL.split(',')[1];
    onCaptureFrame(base64Data);
  };

  const toggleCamera = () => {
    setFacingMode(prev => (prev === 'user' ? 'environment' : 'user'));
  };

  useImperativeHandle(ref, () => ({
    captureFrame,
    toggleCamera
  }));

  return (
    <Box
      position="relative"
      width="100vw"
      height="calc(100vh)"
      bg="black"
      overflow="hidden"
    >
      <video
        ref={videoRef}
        autoPlay
        playsInline
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover'
        }}
      />
    </Box>
  );
});

export default CameraFeed;
