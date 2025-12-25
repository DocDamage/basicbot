import logging
import os
from typing import Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class SafetyCategory(Enum):
    """Safety violation categories."""
    VIOLENCE_HATE = "Violence & Hate"
    SEXUAL_CONTENT = "Sexual Content"
    CRIMINAL_PLANNING = "Criminal Planning"
    GUNS_WEAPONS = "Guns & Weapons"
    SELF_HARM = "Self-Harm"
    PRIVACY_VIOLATION = "Privacy Violation"


class SafetyGuard:
    """
    Safety guard using Llama Guard or alternative safety classifiers.
    Provides content safety checking for user inputs and model outputs.
    """

    CATEGORIES = [
        "Violence & Hate",
        "Sexual Content",
        "Criminal Planning",
        "Guns & Weapons",
        "Self-Harm",
        "Privacy Violation"
    ]

    def __init__(self, model_path: Optional[str] = None, backend: str = "llama_guard"):
        """
        Initialize the safety guard.

        Args:
            model_path: Path to the safety model (optional, will try to download if None)
            backend: Safety backend to use ('llama_guard' or 'simple')
        """
        self.model_path = model_path or os.getenv("LLAMA_GUARD_MODEL_PATH")
        self.backend = backend
        self.model = None
        self.tokenizer = None

        self._initialize_guard()

    def _initialize_guard(self):
        """Initialize the safety guard backend."""
        try:
            if self.backend == "llama_guard":
                self._initialize_llama_guard()
            elif self.backend == "simple":
                self._initialize_simple_guard()
            else:
                logger.warning(f"Unknown backend: {self.backend}, falling back to simple")
                self._initialize_simple_guard()
        except Exception as e:
            logger.error(f"Failed to initialize safety guard: {e}")
            logger.info("Using simple keyword-based safety checking")
            self._initialize_simple_guard()

    def _initialize_llama_guard(self):
        """Initialize Llama Guard model."""
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification

            # Try to load Llama Guard model
            if not self.model_path:
                # Try default model names
                model_names = [
                    "meta-llama/LlamaGuard-7B",
                    "tensorblock/Llama-Guard-3-1B-GGUF",
                    "local_model_path"
                ]

                for model_name in model_names:
                    try:
                        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
                        self.model_path = model_name
                        logger.info(f"Loaded Llama Guard model: {model_name}")
                        break
                    except Exception:
                        continue

                if not self.model:
                    raise Exception("Could not load any Llama Guard model")

            self.classify_method = self._classify_llama_guard

        except ImportError:
            raise ImportError("transformers not installed. Install with: pip install transformers")

    def _initialize_simple_guard(self):
        """Initialize simple keyword-based safety guard."""
        self.classify_method = self._classify_simple
        logger.info("Initialized simple keyword-based safety guard")

    def classify(self, text: str, role: str = "user") -> Dict[str, Any]:
        """
        Classify text for safety violations.

        Args:
            text: Text to classify
            role: Role of the text ('user' or 'assistant')

        Returns:
            Dictionary with safety assessment
        """
        if not self.classify_method:
            return {"safe": True, "category": None, "score": 0.0, "error": "No classifier available"}

        try:
            return self.classify_method(text, role)
        except Exception as e:
            logger.error(f"Error in safety classification: {e}")
            return {"safe": True, "category": None, "score": 0.0, "error": str(e)}

    def _classify_llama_guard(self, text: str, role: str) -> Dict[str, Any]:
        """Classify using Llama Guard model."""
        prompt = self._format_guard_prompt(text, role)

        inputs = self.tokenizer(prompt, return_tensors="pt")

        # Get model predictions
        outputs = self.model(**inputs)
        predictions = outputs.logits.argmax(dim=-1)

        # Llama Guard returns 0 for safe, 1 for unsafe
        is_safe = predictions.item() == 0

        return {
            "safe": is_safe,
            "category": None if is_safe else "Safety violation detected",
            "score": float(predictions.item()),
            "method": "llama_guard"
        }

    def _classify_simple(self, text: str, role: str) -> Dict[str, Any]:
        """Simple keyword-based classification."""
        text_lower = text.lower()

        # Define dangerous keywords and patterns
        dangerous_patterns = {
            SafetyCategory.VIOLENCE_HATE: [
                "kill", "murder", "hate", "racist", "violent", "attack", "bomb",
                "terrorism", "extremist", "supremacist"
            ],
            SafetyCategory.SEXUAL_CONTENT: [
                "sexual abuse", "child exploitation", "porn", "rape", "molest"
            ],
            SafetyCategory.CRIMINAL_PLANNING: [
                "how to", "hack", "steal", "fraud", "launder money", "drug",
                "illegal", "crime", "break in", "robbery"
            ],
            SafetyCategory.GUNS_WEAPONS: [
                "gun", "weapon", "bomb", "explosive", "firearm", "shoot"
            ],
            SafetyCategory.SELF_HARM: [
                "suicide", "kill myself", "self-harm", "cutting", "overdose"
            ],
            SafetyCategory.PRIVACY_VIOLATION: [
                "personal information", "ssn", "social security", "password",
                "confidential", "private data"
            ]
        }

        detected_categories = []
        max_score = 0.0

        # Check for dangerous patterns
        for category, patterns in dangerous_patterns.items():
            matches = sum(1 for pattern in patterns if pattern in text_lower)
            if matches > 0:
                score = min(matches * 0.3, 1.0)  # Cap at 1.0
                detected_categories.append(category.value)
                max_score = max(max_score, score)

        return {
            "safe": len(detected_categories) == 0,
            "category": detected_categories[0] if detected_categories else None,
            "score": max_score,
            "method": "simple_keyword"
        }

    def _format_guard_prompt(self, text: str, role: str) -> str:
        """Format prompt for Llama Guard."""
        return f"""[INST] Task: Check if there is unsafe content in '{role}' messages.

{role} message: {text}

Provide your safety assessment for the {role} message.[/INST]"""

    def is_available(self) -> bool:
        """Check if safety guard is available and initialized."""
        return self.classify_method is not None


class SafetyConfig:
    """Configuration for safety settings."""

    DEFAULT_BACKEND = "simple"  # Use simple by default for compatibility

    @staticmethod
    def create_guard(
        backend: str = DEFAULT_BACKEND,
        model_path: Optional[str] = None
    ) -> SafetyGuard:
        """
        Create a safety guard with specified configuration.

        Args:
            backend: Safety backend ('llama_guard' or 'simple')
            model_path: Path to safety model

        Returns:
            Configured SafetyGuard instance
        """
        return SafetyGuard(model_path=model_path, backend=backend)

    @staticmethod
    def get_available_backends() -> list[str]:
        """Get list of available safety backends."""
        return ["simple", "llama_guard"]


def check_input_safety(
    guard: SafetyGuard,
    text: str,
    role: str = "user"
) -> Tuple[bool, str]:
    """
    Check if input text is safe.

    Args:
        guard: Safety guard instance
        text: Text to check
        role: Role of the text

    Returns:
        Tuple of (is_safe, violation_message)
    """
    result = guard.classify(text, role)

    if result["safe"]:
        return True, ""
    else:
        category = result.get("category", "Unknown violation")
        return False, f"Safety violation detected: {category}"


def check_output_safety(
    guard: SafetyGuard,
    text: str
) -> Tuple[bool, str]:
    """
    Check if model output is safe.

    Args:
        guard: Safety guard instance
        text: Generated text to check

    Returns:
        Tuple of (is_safe, violation_message)
    """
    result = guard.classify(text, role="assistant")

    if result["safe"]:
        return True, ""
    else:
        return False, "Generated content contains unsafe material"
