// src/components/CameraFeed.js
import React, {forwardRef, useEffect, useImperativeHandle, useRef, useState} from 'react';
import {Box, useToast} from '@chakra-ui/react';

const CameraFeed = forwardRef(({ onCaptureFrame }, ref) => {
  const videoRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [facingMode, setFacingMode] = useState('environment'); // Default to back camera
  const [isPortrait, setIsPortrait] = useState(window.innerHeight > window.innerWidth);
  const toast = useToast();

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
        // Enhanced camera constraints for higher resolution
        const constraints = {
          video: {
            facingMode,
            width: { ideal: 1920, min: 1280 },
            height: { ideal: 1080, min: 720 },
            frameRate: { ideal: 30, min: 15 }
          }
        };

        console.log("Requesting camera with constraints:", constraints);
        const newStream = await navigator.mediaDevices.getUserMedia(constraints);

        setStream(newStream);
        if (videoRef.current) {
          videoRef.current.srcObject = newStream;

          // Log the actual camera settings we got
          const videoTracks = newStream.getVideoTracks();
          if (videoTracks.length > 0) {
            const settings = videoTracks[0].getSettings();
            console.log("Camera settings obtained:", settings);
            toast({
              title: "Camera activated",
              description: `Resolution: ${settings.width}x${settings.height}`,
              status: "success",
              duration: 3000,
              isClosable: true,
            });
          }
        }
      } catch (err) {
        console.error(`Error accessing camera with facingMode="${facingMode}":`, err);

        // Try with more relaxed constraints if the initial request fails
        try {
          console.log("Trying with more relaxed camera constraints");
          const fallbackStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode }
          });

          setStream(fallbackStream);
          if (videoRef.current) {
            videoRef.current.srcObject = fallbackStream;
          }

          toast({
            title: "Camera activated with default settings",
            status: "info",
            duration: 3000,
            isClosable: true,
          });
        } catch (fallbackErr) {
          console.error("Failed to initialize camera with fallback settings:", fallbackErr);
          toast({
            title: "Camera error",
            description: "Could not access camera. Please check permissions.",
            status: "error",
            duration: 5000,
            isClosable: true,
          });
        }
      }
    };

    initCamera();
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [facingMode, toast]);

  const captureFrame = () => {
    if (!videoRef.current) return;

    const video = videoRef.current;
    const canvas = document.createElement('canvas');

    // Use the actual video dimensions for highest quality capture
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Quality parameter for JPEG compression (0.8 = 80% quality)
    const dataURL = canvas.toDataURL('image/jpeg', 0.9);
    const base64Data = dataURL.split(',')[1];

    console.log(`Captured frame: ${canvas.width}x${canvas.height}`);
    onCaptureFrame(base64Data);
  };

  const toggleCamera = () => {
    setFacingMode(prev => (prev === 'user' ? 'environment' : 'user'));
    toast({
      title: `Camera switched to ${facingMode === 'user' ? 'back' : 'front'}`,
      status: "info",
      duration: 2000,
      isClosable: true,
    });
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