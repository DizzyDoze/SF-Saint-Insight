// src/App.js
import React, { useState, useRef } from 'react';
import {
  Box,
  Flex,
  IconButton,
  Heading,
  Text,
  useColorMode,
  useColorModeValue,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalCloseButton,
  ModalBody
} from '@chakra-ui/react';
import { SunIcon, MoonIcon, InfoIcon } from '@chakra-ui/icons';
import { FiCamera, FiRotateCw } from 'react-icons/fi';
import CameraFeed from './components/CameraFeed';

function App() {
  // Define color scheme for light and dark modes.
  const darkBg = '#1b1c1c';
  const lightBg = '#eded3';
  const bg = useColorModeValue(lightBg, darkBg);
  
  const { colorMode, toggleColorMode } = useColorMode();

  // Sample detection (bounding box) data
  const [detections, setDetections] = useState([
    {
      id: 1,
      title: 'Sunflower',
      fact: 'Helianthus annuus, grown for its seeds.',
      boundingBox: { x: 0.3, y: 0.1, width: 0.4, height: 0.3 }
    }
  ]);

  // When a frame is captured, send it to the backend.
  const handleCaptureFrame = async (base64Data) => {
    try {
      const response = await fetch('http://127.0.0.1:5000/process_image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: base64Data })
      });
      const result = await response.json();
      setDetections(result.detections || []);
    } catch (error) {
      console.error("Error sending image to backend:", error);
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
          <Heading size="sm">AR AI Education App</Heading>
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

        {/* Render bounding boxes with info bubbles */}
        {detections.map((det) => (
          <Box
            key={det.id}
            position="absolute"
            left={`${det.boundingBox.x * 100}%`}
            top={`${det.boundingBox.y * 100}%`}
            width={`${det.boundingBox.width * 100}%`}
            height={`${det.boundingBox.height * 100}%`}
            border="1px solid rgba(255, 255, 255, 0.8)"
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
              <Text fontSize="sm" mb={2}>
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
        ))}

        {/* Camera Controls in top right corner */}
        <Box position="absolute" top="60px" right="20px" zIndex={3}>
          <Flex direction="column" gap={2}>
            <IconButton
              aria-label="Capture Frame"
              icon={<FiCamera />}
              onClick={() => cameraRef.current && cameraRef.current.captureFrame()}
              variant="solid"
              colorScheme="orange"
            />
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
          <ModalHeader>Quick Tip</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Text>
              Point your camera at an object to learn more! Tap bounding boxes for details.
            </Text>
          </ModalBody>
        </ModalContent>
      </Modal>

      {/* Expanded Info Modal */}
      <Modal isOpen={isInfoOpen} onClose={onInfoClose} size="md" motionPreset="slideInBottom" isCentered>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>{selectedDetection?.title || 'Details'}</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Text mb={2}>
              <strong>Fact: </strong>
              {selectedDetection?.fact || 'No additional information.'}
            </Text>
            <Text mb={4}>
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer nec odio.
              Praesent libero. Sed cursus ante dapibus diam.
            </Text>
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
}

export default App;
