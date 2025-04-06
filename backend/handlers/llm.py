from google import genai


class GeminiWrapper:
    """Simple wrapper for the Gemini vision API"""

    def __init__(self, api_key, model="gemini-2.0-flash"):
        # Initialize the Gemini client with API key
        self.client = genai.Client(api_key=api_key)
        self.model_name = model

    def analyze_image(self, image, prompt):
        """Send image to Gemini API and get text response"""
        try:
            # Send the prompt and image to Gemini's multimodal API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, image]
            )
            return response.text
        except Exception as e:
            print(f"Gemini API error: {e}")
            return f"Error: {e}"