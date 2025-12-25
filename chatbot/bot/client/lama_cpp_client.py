from typing import Any, Iterator

from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

from bot.client.prompt import (
    CTX_PROMPT_TEMPLATE,
    QA_PROMPT_TEMPLATE,
    REFINED_ANSWER_CONVERSATION_AWARENESS_PROMPT_TEMPLATE,
    REFINED_CTX_PROMPT_TEMPLATE,
    REFINED_QUESTION_CONVERSATION_AWARENESS_PROMPT_TEMPLATE,
    TOOL_SYSTEM_TEMPLATE,
    generate_conversation_awareness_prompt,
    generate_ctx_prompt,
    generate_qa_prompt,
    generate_refined_ctx_prompt,
)
from bot.model.base_model import ModelSettings


class LamaCppClient:
    """
    Class for implementing language model client using transformers.
    """

    def __init__(self, model_settings: ModelSettings):
        self.model_settings = model_settings
        self.model_name = model_settings.url  # Use url as model name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name, torch_dtype=torch.float16 if self.device == "cuda" else torch.float32)
        self.model.to(self.device)

    def generate_answer(self, prompt: str, max_new_tokens: int = 512) -> str:
        messages = [
            {"role": "system", "content": self.model_settings.system_template},
            {"role": "user", "content": prompt},
        ]
        input_text = self.tokenizer.apply_chat_template(messages, tokenize=False)
        inputs = self.tokenizer(input_text, return_tensors="pt").to(self.device)
        outputs = self.model.generate(**inputs, max_new_tokens=max_new_tokens, temperature=self.model_settings.config_answer.get("temperature", 0.7), do_sample=True, pad_token_id=self.tokenizer.eos_token_id)
        generated_text = self.tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        return generated_text

    async def async_generate_answer(self, prompt: str, max_new_tokens: int = 512) -> str:
        return self.generate_answer(prompt, max_new_tokens)

    def stream_answer(self, prompt: str, max_new_tokens: int = 512) -> str:
        # For simplicity, return non-streaming
        return self.generate_answer(prompt, max_new_tokens)

    def start_answer_iterator_streamer(self, prompt: str, max_new_tokens: int = 512) -> Iterator[dict]:
        # Simple streaming by yielding tokens
        answer = self.generate_answer(prompt, max_new_tokens)
        for char in answer:
            yield {"choices": [{"delta": {"content": char}}]}

    async def async_start_answer_iterator_streamer(self, prompt: str, max_new_tokens: int = 512) -> Iterator[dict]:
        return self.start_answer_iterator_streamer(prompt, max_new_tokens)

    @staticmethod
    def parse_token(token):
        return token["choices"][0]["delta"].get("content", "")

    @staticmethod
    def generate_qa_prompt(question: str) -> str:
        """
        Generates a question-answering (QA) prompt using predefined templates.

        Args:
            question (str): The question for which the prompt is generated.

        Returns:
            str: The generated QA prompt.
        """
        return generate_qa_prompt(
            template=QA_PROMPT_TEMPLATE,
            question=question,
        )

    @staticmethod
    def generate_ctx_prompt(question: str, context: str) -> str:
        """
        Generates a context-based prompt using predefined templates.

        Args:
            question (str): The question for which the prompt is generated.
            context (str): The context information for the prompt.

        Returns:
            str: The generated context-based prompt.
        """
        return generate_ctx_prompt(
            template=CTX_PROMPT_TEMPLATE,
            question=question,
            context=context,
        )

    @staticmethod
    def generate_refined_ctx_prompt(question: str, context: str, existing_answer: str) -> str:
        """
        Generates a refined prompt for question-answering with existing answer.

        Args:
            question (str): The question for which the prompt is generated.
            context (str): The context information for the prompt.
            existing_answer (str): The existing answer to be refined.

        Returns:
            str: The generated refined prompt.
        """
        return generate_refined_ctx_prompt(
            template=REFINED_CTX_PROMPT_TEMPLATE,
            question=question,
            context=context,
            existing_answer=existing_answer,
        )

    @staticmethod
    def generate_refined_question_conversation_awareness_prompt(question: str, chat_history: str) -> str:
        return generate_conversation_awareness_prompt(
            template=REFINED_QUESTION_CONVERSATION_AWARENESS_PROMPT_TEMPLATE,
            question=question,
            chat_history=chat_history,
        )

    @staticmethod
    def generate_refined_answer_conversation_awareness_prompt(question: str, chat_history: str) -> str:
        return generate_conversation_awareness_prompt(
            template=REFINED_ANSWER_CONVERSATION_AWARENESS_PROMPT_TEMPLATE,
            question=question,
            chat_history=chat_history,
        )

    def retrieve_tools(self, prompt: str, max_new_tokens: int = 512, tools: list[dict] = None, tool_choice: str = None) -> list[dict] | None:
        # Dummy implementation
        return None
