"""
DALL-E 2 image generator module
"""
import time
import requests
from pathlib import Path
from typing import Optional
from openai import OpenAI
import config


class ImageGenerator:
    """Generates images using DALL-E 2 API"""

    def __init__(self):
        """Initialize OpenAI client"""
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.output_dir = config.OUTPUT_DIR

    def generate_image(
        self,
        prompt: str,
        size: str = None,
        quality: str = None,
        max_retries: int = None
    ) -> Optional[str]:
        """
        Generate image using DALL-E 2

        Args:
            prompt: Text prompt for image generation
            size: Image size (256x256, 512x512, 1024x1024)
            quality: Image quality (standard or hd)
            max_retries: Maximum number of retry attempts

        Returns:
            URL of the generated image, or None if failed
        """
        size = size or config.IMAGE_SIZE
        quality = quality or config.IMAGE_QUALITY
        max_retries = max_retries or config.MAX_RETRIES

        # Validate size for DALL-E 2
        valid_sizes = ["256x256", "512x512", "1024x1024"]
        if size not in valid_sizes:
            print(f"Warning: Invalid size {size}. Using 512x512 instead.")
            size = "512x512"

        for attempt in range(max_retries):
            try:
                print(f"Generating image (attempt {attempt + 1}/{max_retries})...")
                print(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

                response = self.client.images.generate(
                    model="dall-e-2",
                    prompt=prompt,
                    size=size,
                    n=1
                )

                image_url = response.data[0].url
                print(f"✓ Image generated successfully: {image_url}")
                return image_url

            except Exception as e:
                print(f"✗ Error generating image (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print("Failed to generate image after all retries.")
                    return None

    def download_image(self, image_url: str, filename: str) -> Optional[Path]:
        """
        Download image from URL and save to local file

        Args:
            image_url: URL of the image
            filename: Name for the saved file (without extension)

        Returns:
            Path to the saved image file, or None if failed
        """
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            # Save to output directory
            file_path = self.output_dir / f"{filename}.png"
            with open(file_path, 'wb') as f:
                f.write(response.content)

            print(f"✓ Image saved to: {file_path}")
            return file_path

        except Exception as e:
            print(f"✗ Error downloading image: {str(e)}")
            return None

    def generate_and_save(
        self,
        prompt: str,
        filename: str,
        size: str = None,
        quality: str = None
    ) -> Optional[str]:
        """
        Generate image and optionally save it locally

        Args:
            prompt: Text prompt for image generation
            filename: Name for the saved file
            size: Image size
            quality: Image quality

        Returns:
            URL of the generated image, or None if failed
        """
        image_url = self.generate_image(prompt, size, quality)

        if image_url:
            # Optionally download and save locally
            self.download_image(image_url, filename)

        return image_url

    def generate_batch(
        self,
        prompts: list,
        filenames: list,
        delay: float = 1.0
    ) -> list:
        """
        Generate multiple images with delay between requests

        Args:
            prompts: List of text prompts
            filenames: List of filenames for saved images
            delay: Delay in seconds between requests

        Returns:
            List of image URLs (None for failed generations)
        """
        if len(prompts) != len(filenames):
            raise ValueError("Number of prompts must match number of filenames")

        results = []
        for i, (prompt, filename) in enumerate(zip(prompts, filenames)):
            print(f"\n--- Generating image {i + 1}/{len(prompts)} ---")
            image_url = self.generate_and_save(prompt, filename)
            results.append(image_url)

            # Add delay between requests (except for the last one)
            if i < len(prompts) - 1:
                print(f"Waiting {delay} seconds before next request...")
                time.sleep(delay)

        return results
