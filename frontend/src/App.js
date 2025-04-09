// src/App.js
import React, {useEffect, useRef, useState} from 'react';
import {
  Box,
  Flex,
  FormControl,
  FormLabel,
  Heading,
  IconButton,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  Spinner,
  Switch,
  Text,
  useColorMode,
  useColorModeValue,
  useDisclosure,
  useToast
} from '@chakra-ui/react';
import {InfoIcon, MoonIcon, SunIcon} from '@chakra-ui/icons';
import {FiCamera, FiRotateCw} from 'react-icons/fi';
import CameraFeed from './components/CameraFeed';
import ReactMarkdown from 'react-markdown'; // Import markdown renderer

// API URL configuration - ensure this matches your backend port
const API_URL = 'http://localhost:8888';

function App() {
  // Define color scheme for light and dark modes
  const darkBg = '#1b1c1c';
  const lightBg = '#eded3';
  const bg = useColorModeValue(lightBg, darkBg);

  const { colorMode, toggleColorMode } = useColorMode();
  const toast = useToast();

  // State for detections and loading state
  const [detections, setDetections] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // Auto-capture is enabled by default now
  const [autoCapture, setAutoCapture] = useState(true);
  const [captureInterval, setCaptureInterval] = useState(5000); // 5 seconds by default

  // When a frame is captured, send it to the backend
  const handleCaptureFrame = async (base64Data) => {
    if (isProcessing) {
      console.log("Already processing a frame, skipping this capture");
      return;
    }

    setIsProcessing(true);
    try {
      const response = await fetch(`${API_URL}/process_image`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: base64Data })
      });

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const result = await response.json();
      console.log("Received analysis result:", result);

      if (result.status === "success" && result.detections && result.detections.length > 0) {
        setDetections(result.detections);
        // Only show toast for manual captures
        if (!autoCapture) {
          toast({
            title: "Analysis complete",
            description: `Found ${result.detections.length} regions`,
            status: "success",
            duration: 3000,
            isClosable: true,
          });
        }
      } else {
        console.warn("No detections found in response:", result);
        // Clear previous detections if none were found
        setDetections([]);
        if (!autoCapture) {
          toast({
            title: "No content detected",
            description: "Try adjusting the camera position",
            status: "info",
            duration: 3000,
            isClosable: true,
          });
        }
      }
    } catch (error) {
      console.error("Error analyzing image:", error);
      if (!autoCapture) {
        // Only show error toast for manual captures
        toast({
          title: "Analysis failed",
          description: error.message || "Could not process the image",
          status: "error",
          duration: 5000,
          isClosable: true,
        });
      }
      // Clear any previous detections when there's an error
      setDetections([]);
    } finally {
      setIsProcessing(false);
    }
  };

  // For expanded info modal (when tapping the info bubble)
  const { isOpen: isInfoOpen, onOpen: onInfoOpen, onClose: onInfoClose } = useDisclosure();
  const [selectedDetection, setSelectedDetection] = useState(null);

  const handleExpand = (det) => {
    setSelectedDetection(det);
    onInfoOpen();
  };

  // For help overlay modal
  const { isOpen: isHelpOpen, onOpen: onHelpOpen, onClose: onHelpClose } = useDisclosure();

  // Create a ref to access CameraFeed methods (capture & toggle)
  const cameraRef = useRef();

  // Auto-capture functionality - now runs by default with a 5-second interval
  useEffect(() => {
    let interval;
    if (autoCapture) {
      interval = setInterval(() => {
        if (cameraRef.current && !isProcessing) {
          cameraRef.current.captureFrame();
        }
      }, captureInterval);

      console.log(`Auto-capture enabled: capturing every ${captureInterval/1000} seconds`);
    }
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [autoCapture, isProcessing, captureInterval]);

  // Function to toggle auto-capture mode
  const toggleAutoCapture = () => {
    setAutoCapture(prev => !prev);
    toast({
      title: !autoCapture ? "Auto-capture enabled" : "Auto-capture disabled",
      status: "info",
      duration: 2000,
      isClosable: true,
    });
  };

  return (
    <Box minH="100vh" bg={bg} position="relative">
      {/* Floating slim header overlay */}
      <Box
        position="absolute"
        top="0"
        left="0"
        width="100%"
        zIndex={3}
        bg={useColorModeValue('rgba(237,237,211,0.8)', 'rgba(27,28,28,0.8)')}
        backdropFilter="blur(8px)"
        px={4}
        py={2}
      >
        <Flex justify="space-between" align="center">
          <Heading size="sm">Classroom Whiteboard Analyzer</Heading>
          <Flex align="center">
            <IconButton
              aria-label="Help"
              icon={<InfoIcon />}
              onClick={onHelpOpen}
              variant="ghost"
              color={colorMode === 'light' ? '#99410b' : 'white'}
              mr={2}
            />
            <IconButton
              aria-label="Toggle Color Mode"
              icon={colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
              onClick={toggleColorMode}
              variant="ghost"
              color={colorMode === 'light' ? '#99410b' : 'white'}
            />
          </Flex>
        </Flex>
      </Box>

      {/* Camera feed container fills the viewport */}
      <Box
        position="absolute"
        top="0"
        left="0"
        width="100vw"
        height="100vh"
        overflow="hidden"
      >
        <CameraFeed ref={cameraRef} onCaptureFrame={handleCaptureFrame} />

        {/* Processing indicator - more subtle in auto mode */}
        {isProcessing && (
          <Box
            position="absolute"
            bottom="16px"
            right="16px"
            bg="rgba(0,0,0,0.7)"
            color="white"
            borderRadius="md"
            p={3}
            zIndex={10}
          >
            <Flex align="center">
              <Spinner size="sm" mr={2} />
              <Text fontSize="sm">Analyzing...</Text>
            </Flex>
          </Box>
        )}

        {/* Render bounding boxes with info bubbles */}
        {detections.map((det) => (
          <React.Fragment key={det.id}>
            {/* Original YOLO detection box - unchanged */}
            <Box
              position="absolute"
              left={`${det.boundingBox.x * 100}%`}
              top={`${det.boundingBox.y * 100}%`}
              width={`${det.boundingBox.width * 100}%`}
              height={`${det.boundingBox.height * 100}%`}
              border="2px solid rgba(255, 255, 255, 0.8)"
              borderRadius="md"
              boxShadow="0 0 8px 2px rgba(255, 255, 255, 0.25)"
              pointerEvents="none"
              zIndex={2}
            >
              <Box
                position="absolute"
                top="0"
                left="0"
                m={2}
                p={3}
                bg="rgba(0,0,0,0.7)"
                color="white"
                borderRadius="md"
                boxShadow="lg"
                pointerEvents="auto"
                maxW="80%"
                _after={{
                  content: '""',
                  position: 'absolute',
                  bottom: '-8px',
                  left: '20px',
                  borderLeft: '8px solid transparent',
                  borderRight: '8px solid transparent',
                  borderTop: '8px solid rgba(0,0,0,0.7)',
                }}
              >
                <Text fontWeight="bold" mb={1} fontSize="md">
                  {det.title}
                </Text>
                <Text fontSize="sm" mb={2} noOfLines={3}>
                  {det.fact}
                </Text>
                <IconButton
                  aria-label="More Info"
                  icon={<InfoIcon />}
                  size="xs"
                  colorScheme="teal"
                  onClick={() => handleExpand(det)}
                />
              </Box>
            </Box>

            {/* New adjacent response box with markdown content */}
            <Box
              position="absolute"
              left={`${(det.boundingBox.x + det.boundingBox.width) * 100}%`}
              top={`${det.boundingBox.y * 100}%`}
              width={`${det.boundingBox.width * 100}%`}
              maxHeight={`${det.boundingBox.height * 100}%`}
              border="2px solid rgba(255, 255, 100, 0.8)"
              borderRadius="md"
              boxShadow="0 0 8px 2px rgba(255, 255, 100, 0.25)"
              zIndex={2}
              pointerEvents="auto"
              bg="rgba(0,0,0,0.7)"
              color="white"
              overflowY="auto"
              p={4}
              m={0}
              css={{
                '&::-webkit-scrollbar': {
                  width: '8px',
                },
                '&::-webkit-scrollbar-track': {
                  width: '10px',
                  background: 'rgba(0,0,0,0.1)',
                },
                '&::-webkit-scrollbar-thumb': {
                  background: 'rgba(255,255,255,0.4)',
                  borderRadius: '24px',
                }
              }}
            >
              <Text fontWeight="bold" mb={2} fontSize="md">
                Full Analysis
              </Text>
              {/* Render markdown content */}
              <Box className="markdown-content">
                <ReactMarkdown>
                  {det.full_text}
                </ReactMarkdown>
              </Box>
            </Box>
          </React.Fragment>
        ))}

        {/* Camera Controls in top right corner */}
        <Box position="absolute" top="60px" right="20px" zIndex={3}>
          <Flex direction="column" gap={2}>
            {/* Auto-capture toggle switch */}
            <Box
              bg="rgba(0,0,0,0.7)"
              p={2}
              borderRadius="md"
              color="white"
            >
              <FormControl display="flex" alignItems="center">
                <FormLabel mb="0" fontSize="xs">
                  Auto
                </FormLabel>
                <Switch
                  colorScheme="orange"
                  size="sm"
                  isChecked={autoCapture}
                  onChange={toggleAutoCapture}
                />
              </FormControl>
            </Box>

            {/* Manual capture button - only needed when auto is off */}
            <IconButton
              aria-label="Capture Frame"
              icon={<FiCamera />}
              onClick={() => cameraRef.current && cameraRef.current.captureFrame()}
              variant="solid"
              colorScheme="orange"
              isDisabled={isProcessing}
            />

            {/* Camera flip button */}
            <IconButton
              aria-label="Flip Camera"
              icon={<FiRotateCw />}
              onClick={() => cameraRef.current && cameraRef.current.toggleCamera()}
              variant="solid"
              colorScheme="orange"
            />
          </Flex>
        </Box>
      </Box>

      {/* Help Modal */}
      <Modal isOpen={isHelpOpen} onClose={onHelpClose} isCentered>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>How to Use</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <Text mb={3}>
              This app automatically analyzes classroom whiteboard content in real-time:
            </Text>
            <Text mb={2}>
              1. Point your camera at a whiteboard with equations, diagrams, or text
            </Text>
            <Text mb={2}>
              2. The app will automatically analyze content every 5 seconds
            </Text>
            <Text mb={2}>
              3. Each detection has two boxes: a detection box (white border) and an analysis box (yellow border)
            </Text>
            <Text mb={2}>
              4. The analysis box shows the complete markdown-formatted response
            </Text>
            <Text mb={2}>
              5. Toggle the "Auto" switch to enable/disable automatic captures
            </Text>
            <Text>
              Use the flip camera button to switch between front and rear cameras.
            </Text>
          </ModalBody>
        </ModalContent>
      </Modal>

      {/* Expanded Info Modal - keep this as a fallback option */}
      <Modal isOpen={isInfoOpen} onClose={onInfoClose} size="md" motionPreset="slideInBottom" isCentered>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>{selectedDetection?.title || 'Analysis'}</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            {selectedDetection?.full_text ? (
              <Text>
                {selectedDetection.full_text}
              </Text>
            ) : (
              <Text>
                {selectedDetection?.fact || 'No detailed analysis available.'}
              </Text>
            )}
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
}

export default App;