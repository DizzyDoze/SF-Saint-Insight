import io
import time

import google.generativeai as genai
from PIL import Image


class GeminiWrapper:
    """Enhanced wrapper for the Gemini vision API with retry logic and image optimization"""

    def __init__(self, api_key, model="gemini-2.0-flash", max_retries=2):
        # Initialize the Gemini client with API key
        genai.configure(api_key=api_key)
        self.model_name = model
        self.max_retries = max_retries
        self.max_image_size = (2048, 2048)  # Maximum recommended size for Gemini
        print(f"Initialized Gemini wrapper with model: {model}")

        # Test the API connection
        try:
            model = genai.GenerativeModel(self.model_name)
            print("Successfully connected to Gemini API")
        except Exception as e:
            print(f"Warning: Could not initialize Gemini API: {e}")

    def _optimize_image(self, image):
        """Optimize image for the Gemini API to handle larger images efficiently"""
        try:
            # Get original size
            original_width, original_height = image.size
            print(f"Original image size: {original_width}x{original_height}")

            # Check if we need to resize
            if original_width > self.max_image_size[0] or original_height > self.max_image_size[1]:
                # Calculate the scaling factor
                scale_factor = min(
                    self.max_image_size[0] / original_width,
                    self.max_image_size[1] / original_height
                )

                # Apply scaling
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"Resized image to: {new_width}x{new_height}")

                # Convert to buffer
                img_buffer = io.BytesIO()
                resized_image.save(img_buffer, format='JPEG', quality=90)
                img_buffer.seek(0)
                return Image.open(img_buffer)
            else:
                return image

        except Exception as e:
            print(f"Error optimizing image: {e}")
            return image  # Return original image if optimization fails

    def analyze_image(self, image, prompt, retry_count=0):
        """Send image to Gemini API and get text response with retry logic"""
        try:
            print(f"Creating Gemini model instance: {self.model_name}")
            # Create a generative model instance
            model = genai.GenerativeModel(self.model_name)

            # Optimize the image for better processing
            optimized_image = self._optimize_image(image)

            print("Sending image to Gemini API...")
            # Send the prompt and image to Gemini's multimodal API
            start_time = time.time()
            response = model.generate_content(
                contents=[prompt, optimized_image]
            )
            elapsed = time.time() - start_time
            print(f"Received response from Gemini API in {elapsed:.2f} seconds")

            if hasattr(response, 'text'):
                return response.text
            else:
                print(f"Unexpected response format: {response}")
                return "Error: Unexpected response format from Gemini API"

        except Exception as e:
            print(f"Gemini API error: {e}")

            # Implement retry logic for transient errors
            if retry_count < self.max_retries:
                retry_count += 1
                wait_time = 2 ** retry_count  # Exponential backoff
                print(f"Retrying ({retry_count}/{self.max_retries}) in {wait_time} seconds...")
                time.sleep(wait_time)
                return self.analyze_image(image, prompt, retry_count)

            return f"Error: {e}"