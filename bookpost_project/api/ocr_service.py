"""
OCR Service for extracting text from book page images.
Supports both Google Cloud Vision and Gemini AI.
"""
import os
import base64
import re
from typing import List, Tuple
from django.conf import settings


class OCRService:
    """Service class for OCR text extraction."""

    def __init__(self):
        self.gemini_api_key = settings.GEMINI_API_KEY
        self.use_gemini = bool(self.gemini_api_key)

    def extract_text_from_image(self, image_path: str) -> str:
        """
        Extract text from image file.

        Args:
            image_path: Path to the image file

        Returns:
            Extracted text as string
        """
        if self.use_gemini:
            return self._extract_with_gemini(image_path)
        else:
            return self._extract_with_vision_api(image_path)

    def _extract_with_gemini(self, image_path: str) -> str:
        """
        Extract text using Google Gemini API.

        Args:
            image_path: Path to the image file

        Returns:
            Extracted text
        """
        try:
            import google.generativeai as genai

            # Configure Gemini
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')

            # Read and encode image
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()

            # Prepare prompt for text extraction
            prompt = """Extract and transcribe all the text from this book page image.
            Maintain the paragraph structure. If there are headings, format them as markdown headings.
            Only return the extracted text, no additional commentary."""

            # Generate content
            response = model.generate_content([prompt, {'mime_type': 'image/jpeg', 'data': image_data}])

            return response.text.strip()

        except ImportError:
            raise Exception(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )
        except Exception as e:
            raise Exception(f"Gemini OCR failed: {str(e)}")

    def _extract_with_vision_api(self, image_path: str) -> str:
        """
        Extract text using Google Cloud Vision API.

        Args:
            image_path: Path to the image file

        Returns:
            Extracted text
        """
        try:
            from google.cloud import vision

            # Initialize Vision API client
            client = vision.ImageAnnotatorClient()

            # Read image file
            with open(image_path, 'rb') as image_file:
                content = image_file.read()

            image = vision.Image(content=content)

            # Perform text detection
            response = client.document_text_detection(image=image)

            if response.error.message:
                raise Exception(f"Vision API error: {response.error.message}")

            # Extract full text
            text = response.full_text_annotation.text

            return text.strip()

        except ImportError:
            raise Exception(
                "google-cloud-vision package not installed. "
                "Install with: pip install google-cloud-vision"
            )
        except Exception as e:
            raise Exception(f"Vision API OCR failed: {str(e)}")

    def parse_into_paragraphs(self, text: str) -> List[str]:
        """
        Parse extracted text into logical paragraphs.

        Args:
            text: Raw extracted text

        Returns:
            List of paragraph strings
        """
        # Split by double newlines or multiple spaces
        paragraphs = re.split(r'\n\s*\n+', text)

        # Clean and filter paragraphs
        cleaned_paragraphs = []
        for para in paragraphs:
            # Remove extra whitespace
            para = ' '.join(para.split())

            # Skip very short paragraphs (likely noise)
            if len(para) > 20:
                cleaned_paragraphs.append(para)

        return cleaned_paragraphs

    def extract_and_parse(self, image_path: str) -> Tuple[str, List[str]]:
        """
        Extract text from image and parse into paragraphs.

        Args:
            image_path: Path to the image file

        Returns:
            Tuple of (raw_text, list_of_paragraphs)
        """
        raw_text = self.extract_text_from_image(image_path)
        paragraphs = self.parse_into_paragraphs(raw_text)

        return raw_text, paragraphs


# Global instance
ocr_service = OCRService()
