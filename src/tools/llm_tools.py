"""LLM interaction tools"""

from typing import List, Dict, Optional, Iterator, Any
import ollama
import os


def call_llm(
    prompt: str,
    model: str = "llama3.2:1b",
    provider: str = "ollama",
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    **kwargs
) -> str:
    """
    Call LLM and get response
    
    Args:
        prompt: User prompt
        model: Model name
        provider: Provider (ollama, openai, etc.)
        system_prompt: Optional system prompt
        temperature: Temperature for generation
        **kwargs: Additional parameters
        
    Returns:
        LLM response text
    """
    if provider == "ollama":
        return _call_ollama(prompt, model, system_prompt, temperature, **kwargs)
    elif provider == "openai":
        return _call_openai(prompt, model, system_prompt, temperature, **kwargs)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def stream_llm(
    prompt: str,
    model: str = "llama3.2:1b",
    provider: str = "ollama",
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    **kwargs
) -> Iterator[str]:
    """
    Stream LLM response
    
    Args:
        prompt: User prompt
        model: Model name
        provider: Provider (ollama, openai, etc.)
        system_prompt: Optional system prompt
        temperature: Temperature for generation
        **kwargs: Additional parameters
        
    Yields:
        Chunks of LLM response text
    """
    if provider == "ollama":
        yield from _stream_ollama(prompt, model, system_prompt, temperature, **kwargs)
    elif provider == "openai":
        yield from _stream_openai(prompt, model, system_prompt, temperature, **kwargs)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def _call_ollama(
    prompt: str,
    model: str,
    system_prompt: Optional[str],
    temperature: float,
    **kwargs
) -> str:
    """Call Ollama API"""
    try:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        client = ollama.Client(host=base_url)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat(
            model=model,
            messages=messages,
            options={
                "temperature": temperature,
                **kwargs
            }
        )
        
        return response["message"]["content"]
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return f"Error: {str(e)}"


def _stream_ollama(
    prompt: str,
    model: str,
    system_prompt: Optional[str],
    temperature: float,
    **kwargs
) -> Iterator[str]:
    """Stream from Ollama API"""
    try:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        client = ollama.Client(host=base_url)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        stream = client.chat(
            model=model,
            messages=messages,
            stream=True,
            options={
                "temperature": temperature,
                **kwargs
            }
        )
        
        for chunk in stream:
            if "message" in chunk and "content" in chunk["message"]:
                yield chunk["message"]["content"]
    except Exception as e:
        print(f"Error streaming from Ollama: {e}")
        yield f"Error: {str(e)}"


def _call_openai(
    prompt: str,
    model: str,
    system_prompt: Optional[str],
    temperature: float,
    **kwargs
) -> str:
    """Call OpenAI API"""
    try:
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        client = OpenAI(api_key=api_key)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            **kwargs
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return f"Error: {str(e)}"


def _stream_openai(
    prompt: str,
    model: str,
    system_prompt: Optional[str],
    temperature: float,
    **kwargs
) -> Iterator[str]:
    """Stream from OpenAI API"""
    try:
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        client = OpenAI(api_key=api_key)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True,
            **kwargs
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        print(f"Error streaming from OpenAI: {e}")
        yield f"Error: {str(e)}"

