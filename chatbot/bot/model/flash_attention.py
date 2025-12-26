import logging
import time
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class FlashAttentionTester:
    """
    Utility class for testing and benchmarking Flash Attention performance.
    Provides compatibility checking and performance benchmarking.
    """

    def __init__(self):
        self.compatibility_info = self._check_compatibility()

    def _check_compatibility(self) -> Dict[str, Any]:
        """
        Check if Flash Attention is compatible with the current system.

        Returns:
            Dictionary with compatibility information
        """
        info = {
            "cuda_available": False,
            "cuda_version": None,
            "gpu_name": None,
            "flash_attention_supported": False,
            "flash_attention_available": False,
            "recommended": False
        }

        try:
            import torch

            info["cuda_available"] = torch.cuda.is_available()

            if info["cuda_available"]:
                info["cuda_version"] = torch.version.cuda
                info["gpu_name"] = torch.cuda.get_device_name(0)

                # Check CUDA version (Flash Attention 2 requires 11.4+)
                if info["cuda_version"]:
                    cuda_major, cuda_minor = map(int, info["cuda_version"].split('.')[:2])
                    cuda_version_float = cuda_major + cuda_minor / 10
                    info["flash_attention_supported"] = cuda_version_float >= 11.4

                # Check GPU architecture (Ampere 30xx or newer recommended)
                gpu_name = info["gpu_name"].lower()
                is_ampere_or_newer = any(arch in gpu_name for arch in [
                    'rtx 30', 'rtx 40', 'a100', 'a6000', 'h100', 'l40'
                ])
                info["flash_attention_supported"] = info["flash_attention_supported"] and is_ampere_or_newer

                # Check if flash-attn package is available
                try:
                    import flash_attn
                    info["flash_attention_available"] = True
                    logger.info("flash-attn package is available")
                except ImportError:
                    info["flash_attention_available"] = False
                    logger.warning("flash-attn package not installed")

                info["recommended"] = info["flash_attention_supported"] and info["flash_attention_available"]

        except ImportError:
            logger.warning("PyTorch not available for Flash Attention compatibility check")

        return info

    def is_compatible(self) -> bool:
        """Check if Flash Attention can be used on this system."""
        return self.compatibility_info.get("recommended", False)

    def get_compatibility_info(self) -> Dict[str, Any]:
        """Get detailed compatibility information."""
        return self.compatibility_info.copy()

    def benchmark_inference(
        self,
        model,
        tokenizer,
        prompt: str,
        num_runs: int = 5,
        max_new_tokens: int = 512
    ) -> Dict[str, float]:
        """
        Benchmark inference performance with timing.

        Args:
            model: The transformer model to benchmark
            tokenizer: The tokenizer for the model
            prompt: Input prompt for generation
            num_runs: Number of benchmark runs
            max_new_tokens: Maximum tokens to generate

        Returns:
            Dictionary with benchmark statistics
        """
        if not self.is_compatible():
            logger.warning("Flash Attention not recommended for this system")
            return {"error": "Flash Attention not compatible"}

        times = []

        try:
            for i in range(num_runs):
                start_time = time.time()

                inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
                with torch.no_grad():
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=max_new_tokens,
                        do_sample=False,
                        use_cache=True
                    )

                torch.cuda.synchronize()  # Wait for GPU operations to complete
                end_time = time.time()

                execution_time = end_time - start_time
                times.append(execution_time)
                logger.info(f"Benchmark run {i + 1}/{num_runs}: {execution_time:.4f}s")

            import numpy as np

            return {
                "mean_time": round(np.mean(times), 4),
                "std_time": round(np.std(times), 4),
                "min_time": round(np.min(times), 4),
                "max_time": round(np.max(times), 4),
                "num_runs": num_runs,
                "tokens_generated": max_new_tokens,
                "tokens_per_second": round(max_new_tokens / np.mean(times), 2)
            }

        except Exception as e:
            logger.error(f"Error during benchmarking: {e}")
            return {"error": str(e)}

    def compare_models(
        self,
        model_with_flash,
        model_without_flash,
        tokenizer,
        prompt: str,
        num_runs: int = 3,
        max_new_tokens: int = 256
    ) -> Dict[str, Any]:
        """
        Compare performance between Flash Attention and standard attention.

        Args:
            model_with_flash: Model with Flash Attention enabled
            model_without_flash: Model with standard attention
            tokenizer: Tokenizer for both models
            prompt: Input prompt
            num_runs: Number of benchmark runs
            max_new_tokens: Maximum tokens to generate

        Returns:
            Comparison results dictionary
        """
        logger.info("Benchmarking model with Flash Attention...")
        flash_results = self.benchmark_inference(
            model_with_flash, tokenizer, prompt, num_runs, max_new_tokens
        )

        logger.info("Benchmarking model with standard attention...")
        standard_results = self.benchmark_inference(
            model_without_flash, tokenizer, prompt, num_runs, max_new_tokens
        )

        if "error" in flash_results or "error" in standard_results:
            return {
                "error": "Benchmarking failed",
                "flash_results": flash_results,
                "standard_results": standard_results
            }

        speedup = standard_results["mean_time"] / flash_results["mean_time"]

        return {
            "flash_attention_time": flash_results["mean_time"],
            "standard_attention_time": standard_results["mean_time"],
            "speedup_factor": round(speedup, 2),
            "flash_tokens_per_second": flash_results["tokens_per_second"],
            "standard_tokens_per_second": standard_results["tokens_per_second"],
            "improvement_percentage": round((1 - flash_results["mean_time"] / standard_results["mean_time"]) * 100, 1)
        }


def check_flash_attention_compatibility() -> Tuple[bool, str]:
    """
    Quick compatibility check function.

    Returns:
        Tuple of (is_compatible, message)
    """
    tester = FlashAttentionTester()
    info = tester.get_compatibility_info()

    if not info["cuda_available"]:
        return False, "CUDA not available"

    if not info["flash_attention_supported"]:
        gpu = info.get("gpu_name", "Unknown GPU")
        cuda = info.get("cuda_version", "Unknown CUDA")
        return False, f"Not supported on {gpu} with CUDA {cuda}"

    if not info["flash_attention_available"]:
        return False, "flash-attn package not installed"

    gpu = info.get("gpu_name", "GPU")
    return True, f"Compatible with {gpu}"


def create_model_with_flash_attention(model_name: str, **kwargs):
    """
    Create a transformer model with Flash Attention enabled.

    Args:
        model_name: HuggingFace model name
        **kwargs: Additional arguments for model loading

    Returns:
        Model with Flash Attention enabled (if compatible)
    """
    tester = FlashAttentionTester()

    if not tester.is_compatible():
        logger.warning("Flash Attention not compatible, falling back to standard attention")
        return None

    try:
        from transformers import AutoModelForCausalLM

        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="auto",  # Use bfloat16 if available
            device_map="auto",
            attn_implementation="flash_attention_2",
            **kwargs
        )

        logger.info(f"Loaded model {model_name} with Flash Attention 2")
        return model

    except Exception as e:
        logger.error(f"Failed to load model with Flash Attention: {e}")
        return None


def create_model_without_flash_attention(model_name: str, **kwargs):
    """
    Create a transformer model with standard attention.

    Args:
        model_name: HuggingFace model name
        **kwargs: Additional arguments for model loading

    Returns:
        Model with standard attention
    """
    try:
        from transformers import AutoModelForCausalLM

        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="auto",
            device_map="auto",
            **kwargs
        )

        logger.info(f"Loaded model {model_name} with standard attention")
        return model

    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return None
