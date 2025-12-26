import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
import tempfile
import os

logger = logging.getLogger(__name__)


class VisionLLMClient:
    """
    Multimodal LLM client supporting image analysis.
    Uses various vision-capable models as Llama 3.2 Vision is not yet available in llama.cpp.
    """

    def __init__(
        self,
        model_name: str = "llava-hf/llava-1.5-7b-hf",
        device: str = "auto"
    ):
        """
        Initialize the vision client.

        Args:
            model_name: Name of the vision model to use
            device: Device to run the model on ('auto', 'cpu', 'cuda')
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self.processor = None
        self.is_available = False

        self._initialize_model()

    def _initialize_model(self):
        """Initialize the vision model."""
        try:
            # Try LLaVA first (most compatible with transformers)
            if "llava" in self.model_name.lower():
                self._initialize_llava()
            elif "jina" in self.model_name.lower():
                self._initialize_jina()
            else:
                # Fallback to LLaVA
                self._initialize_llava()

        except Exception as e:
            logger.error(f"Failed to initialize vision model: {e}")
            self.is_available = False

    def _initialize_llava(self):
        """Initialize LLaVA model."""
        try:
            from transformers import LlavaForConditionalGeneration, AutoProcessor
            import torch

            logger.info(f"Loading LLaVA model: {self.model_name}")

            # Determine device
            if self.device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                device = self.device

            self.model = LlavaForConditionalGeneration.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map=device if device == "cuda" else None,
                low_cpu_mem_usage=True
            )

            if device == "cpu":
                self.model = self.model.to(device)

            self.processor = AutoProcessor.from_pretrained(self.model_name)
            self.is_available = True
            self.model_type = "llava"

            logger.info(f"LLaVA model loaded successfully on {device}")

        except ImportError:
            raise ImportError("transformers not installed. Install with: pip install transformers")
        except Exception as e:
            logger.error(f"Error loading LLaVA model: {e}")
            raise

    def _initialize_jina(self):
        """Initialize Jina VLM."""
        try:
            from transformers import AutoModel, AutoTokenizer
            import torch

            logger.info(f"Loading Jina VLM: {self.model_name}")

            # Determine device
            if self.device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                device = self.device

            # Jina models might have different loading procedures
            # This is a placeholder for Jina-specific initialization
            self.model = AutoModel.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map=device if device == "cuda" else None
            )

            if device == "cpu":
                self.model = self.model.to(device)

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.is_available = True
            self.model_type = "jina"

            logger.info(f"Jina VLM loaded successfully on {device}")

        except Exception as e:
            logger.error(f"Error loading Jina VLM: {e}")
            raise

    def generate_with_image(
        self,
        text: str,
        image_path: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text response based on text prompt and image.

        Args:
            text: Text prompt describing what to do with the image
            image_path: Path to the image file
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text response
        """
        if not self.is_available:
            return "Vision model is not available. Please check the model configuration."

        if not os.path.exists(image_path):
            return f"Image file not found: {image_path}"

        try:
            if self.model_type == "llava":
                return self._generate_llava(text, image_path, max_new_tokens, temperature)
            elif self.model_type == "jina":
                return self._generate_jina(text, image_path, max_new_tokens, temperature)
            else:
                return "Unsupported model type"

        except Exception as e:
            logger.error(f"Error generating with image: {e}")
            return f"Error processing image: {str(e)}"

    def _generate_llava(
        self,
        text: str,
        image_path: str,
        max_new_tokens: int,
        temperature: float
    ) -> str:
        """Generate using LLaVA model."""
        from PIL import Image

        # Load and process image
        image = Image.open(image_path)

        # Create prompt in LLaVA format
        prompt = f"<image>\n{text}"

        # Process inputs
        inputs = self.processor(text=prompt, images=image, return_tensors="pt")

        # Move to same device as model
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        # Generate
        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                pad_token_id=self.processor.tokenizer.pad_token_id
            )

        # Decode response
        response = self.processor.decode(output[0], skip_special_tokens=True)

        # Clean up the response (remove the prompt part)
        if prompt in response:
            response = response.split(prompt, 1)[-1].strip()

        return response

    def _generate_jina(
        self,
        text: str,
        image_path: str,
        max_new_tokens: int,
        temperature: float
    ) -> str:
        """Generate using Jina VLM."""
        # Placeholder for Jina-specific generation
        # Jina models might have different APIs
        return "Jina VLM generation not yet implemented"

    def analyze_image(
        self,
        image_path: str,
        analysis_type: str = "describe",
        max_new_tokens: int = 300
    ) -> str:
        """
        Analyze an image with predefined analysis types.

        Args:
            image_path: Path to the image
            analysis_type: Type of analysis ('describe', 'ocr', 'classify', 'detect')
            max_new_tokens: Maximum tokens for response

        Returns:
            Analysis result
        """
        prompts = {
            "describe": "Describe this image in detail, including objects, colors, composition, and any text visible.",
            "ocr": "Extract all text visible in this image. Return only the text, no descriptions.",
            "classify": "Classify this image. What category or type of image is this? Provide a brief explanation.",
            "detect": "Detect and list all objects visible in this image."
        }

        prompt = prompts.get(analysis_type, prompts["describe"])

        return self.generate_with_image(
            prompt,
            image_path,
            max_new_tokens=max_new_tokens
        )

    def extract_text_from_image(self, image_path: str) -> str:
        """
        Extract text from an image using OCR-like capabilities.

        Args:
            image_path: Path to the image

        Returns:
            Extracted text
        """
        return self.analyze_image(image_path, "ocr", max_new_tokens=200)

    def describe_image(self, image_path: str) -> str:
        """
        Generate a detailed description of an image.

        Args:
            image_path: Path to the image

        Returns:
            Image description
        """
        return self.analyze_image(image_path, "describe", max_new_tokens=400)


class ImageProcessor:
    """
    Utility class for image processing and management.
    """

    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']

    @staticmethod
    def is_supported_image(file_path: str) -> bool:
        """Check if the file is a supported image format."""
        if not file_path:
            return False

        file_ext = Path(file_path).suffix.lower()
        return file_ext in ImageProcessor.SUPPORTED_FORMATS

    @staticmethod
    def save_uploaded_image(uploaded_file) -> str:
        """
        Save an uploaded Streamlit file to a temporary location.

        Args:
            uploaded_file: Streamlit uploaded file object

        Returns:
            Path to the saved image file
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                return tmp_file.name
        except Exception as e:
            logger.error(f"Error saving uploaded image: {e}")
            return ""

    @staticmethod
    def cleanup_temp_image(file_path: str):
        """Clean up temporary image file."""
        try:
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            logger.error(f"Error cleaning up temp image: {e}")


class MultimodalRAG:
    """
    RAG system extended with multimodal capabilities.
    Can process both text and images.
    """

    def __init__(
        self,
        text_vector_db,
        vision_client: Optional[VisionLLMClient] = None
    ):
        """
        Initialize multimodal RAG.

        Args:
            text_vector_db: Text-based vector database
            vision_client: Vision-capable LLM client
        """
        self.text_vector_db = text_vector_db
        self.vision_client = vision_client

        # Store for processed images
        self.image_store = {}

    def process_image(
        self,
        image_path: str,
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Process an image and extract information.

        Args:
            image_path: Path to the image
            user_id: User identifier for storing results

        Returns:
            Dictionary with image analysis results
        """
        if not self.vision_client or not self.vision_client.is_available:
            return {"error": "Vision capabilities not available"}

        try:
            # Analyze the image
            description = self.vision_client.describe_image(image_path)
            extracted_text = self.vision_client.extract_text_from_image(image_path)

            # Store results
            image_info = {
                "description": description,
                "extracted_text": extracted_text,
                "path": image_path,
                "user_id": user_id,
                "timestamp": str(datetime.now())
            }

            # Store in vector database if there's extracted text
            if extracted_text.strip():
                from entities.document import Document
                image_doc = Document(
                    page_content=f"Image content: {extracted_text}\nDescription: {description}",
                    metadata={
                        "source": image_path,
                        "type": "image",
                        "user_id": user_id,
                        "description": description
                    }
                )
                self.text_vector_db.from_chunks([image_doc])

            return image_info

        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return {"error": str(e)}

    def search_with_image(
        self,
        query: str,
        image_path: Optional[str] = None,
        k: int = 4
    ) -> tuple:
        """
        Perform multimodal search combining text query with optional image.

        Args:
            query: Text query
            image_path: Optional image to include in search
            k: Number of results to return

        Returns:
            Tuple of (documents, sources)
        """
        # Start with text-based search
        docs, sources = self.text_vector_db.similarity_search_with_threshold(
            query=query, k=k
        )

        # If image is provided, enhance the search
        if image_path and self.vision_client and self.vision_client.is_available:
            try:
                # Get image description
                image_description = self.vision_client.describe_image(image_path)

                # Combine with text query
                multimodal_query = f"{query}\nImage context: {image_description}"

                # Search again with enhanced query
                enhanced_docs, enhanced_sources = self.text_vector_db.similarity_search_with_threshold(
                    query=multimodal_query, k=k
                )

                # Merge results (prioritize enhanced results)
                all_docs = enhanced_docs + docs
                all_sources = enhanced_sources + sources

                # Remove duplicates and limit results
                seen_contents = set()
                unique_docs = []
                unique_sources = []

                for doc, source in zip(all_docs, all_sources):
                    content = doc.page_content[:200]  # Use first 200 chars as identifier
                    if content not in seen_contents:
                        seen_contents.add(content)
                        unique_docs.append(doc)
                        unique_sources.append(source)

                return unique_docs[:k], unique_sources[:k]

            except Exception as e:
                logger.error(f"Error in multimodal search: {e}")
                # Fall back to text-only search

        return docs, sources


# Import here to avoid circular imports
try:
    import torch
    from datetime import datetime
except ImportError:
    torch = None
    datetime = None
