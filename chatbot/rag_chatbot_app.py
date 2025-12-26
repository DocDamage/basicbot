import argparse
import sys
import time
from pathlib import Path

import streamlit as st
from bot.client.lama_cpp_client import LamaCppClient
from bot.conversation.chat_history import ChatHistory
from bot.conversation.conversation_handler import answer_with_context, extract_content_after_reasoning, refine_question
from bot.conversation.ctx_strategy import (
    BaseSynthesisStrategy,
    get_ctx_synthesis_strategies,
    get_ctx_synthesis_strategy,
)
from bot.agent.agent import Agent, AgentConfig
from bot.client.vision_client import VisionLLMClient, ImageProcessor, MultimodalRAG
from bot.memory.embedder import Embedder
from bot.memory.long_term_memory import LongTermMemory, MemoryManager
from bot.memory.reranker import Reranker, RerankerConfig
from bot.memory.vector_database.chroma import Chroma
from bot.model.flash_attention import FlashAttentionTester, check_flash_attention_compatibility
from bot.model.model_registry import get_model_settings, get_models
from bot.safety.guard import SafetyGuard, SafetyConfig, check_input_safety, check_output_safety
from bot.tools.google_search import GoogleSearchTool, SearchAugmentedRAG
from bot.tools.registry import create_default_tool_registry
from helpers.log import get_logger
from helpers.prettier import prettify_source

logger = get_logger(__name__)

st.set_page_config(page_title="RAG Chatbot", page_icon="💬", initial_sidebar_state="collapsed")


@st.cache_resource()
def load_llm_client(model_name: str, use_flash_attention: bool = False) -> LamaCppClient:
    model_settings = get_model_settings(model_name)

    # Flash Attention is only applicable to transformers-based models, not LlamaCpp
    # LlamaCpp uses GGUF models which have their own optimizations
    if use_flash_attention:
        st.sidebar.info("Note: Flash Attention is for transformers models, not applicable to LlamaCpp")

    llm = LamaCppClient(model_settings=model_settings)
    return llm


@st.cache_resource()
def init_chat_history(total_length: int = 2) -> ChatHistory:
    chat_history = ChatHistory(total_length=total_length)
    return chat_history


@st.cache_resource()
def load_ctx_synthesis_strategy(ctx_synthesis_strategy_name: str, _llm: LamaCppClient) -> BaseSynthesisStrategy:
    ctx_synthesis_strategy = get_ctx_synthesis_strategy(ctx_synthesis_strategy_name, llm=_llm)
    return ctx_synthesis_strategy


@st.cache_resource()
def load_index(vector_store_path: Path) -> Chroma:
    """
    Loads a Vector Database index based on the specified vector store path.

    Args:
        vector_store_path (Path): The path to the vector store.

    Returns:
        Chroma: An instance of the Vector Database.
    """
    embedding = Embedder()
    index = Chroma(persist_directory=str(vector_store_path), embedding=embedding)

    return index


def init_page(root_folder: Path) -> None:
    """
    Initializes the page configuration for the application.
    """
    left_column, central_column, right_column = st.columns([2, 1, 2])

    with left_column:
        st.write(" ")

    with central_column:
        st.image(str(root_folder / "images/bot.png"), width="auto")
        st.markdown("""<h4 style='text-align: center; color: grey;'></h4>""", unsafe_allow_html=True)

    with right_column:
        st.write(" ")

    st.sidebar.title("Options")


@st.cache_resource
def init_welcome_message() -> None:
    """
    Initializes a welcome message for the chat interface.
    """
    with st.chat_message("assistant"):
        st.write("How can I help you today?")


def reset_chat_history(chat_history: ChatHistory) -> None:
    """
    Initializes the chat history, allowing users to clear the conversation.
    """
    clear_button = st.sidebar.button("🗑️ Clear Conversation", key="clear")
    if clear_button or "messages" not in st.session_state:
        st.session_state.messages = []
        chat_history.clear()


def display_messages_from_history():
    """
    Displays chat messages from the history on app rerun.
    """
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def main(parameters) -> None:
    """
    Main function to run the RAG Chatbot application.

    Args:
        parameters: Parameters for the application.
    """
    root_folder = Path(__file__).resolve().parent.parent
    model_folder = root_folder / "models"
    vector_store_path = root_folder / "vector_store" / "docs_index"
    Path(model_folder).parent.mkdir(parents=True, exist_ok=True)

    model_name = parameters.model
    synthesis_strategy_name = parameters.synthesis_strategy
    max_new_tokens = parameters.max_new_tokens

    init_page(root_folder)
    llm = load_llm_client(model_name)
    chat_history = init_chat_history(2)
    ctx_synthesis_strategy = load_ctx_synthesis_strategy(synthesis_strategy_name, _llm=llm)
    index = load_index(vector_store_path)
    reset_chat_history(chat_history)
    init_welcome_message()
    display_messages_from_history()

    # Reranker configuration
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔄 Reranking Options")
    use_reranker = st.sidebar.checkbox("Enable Reranking", value=False)

    reranker_backend = None
    reranker = None
    if use_reranker:
        reranker_backend = st.sidebar.selectbox(
            "Reranker Backend",
            ["flashrank", "jinai"],
            help="Choose reranking algorithm"
        )

        try:
            reranker_config = RerankerConfig.get_default_config(reranker_backend)
            reranker = Reranker(**reranker_config)

            if reranker.is_available():
                st.sidebar.success(f"✅ {reranker_backend.title()} reranker loaded")
            else:
                st.sidebar.warning(f"⚠️ {reranker_backend.title()} reranker not available")
                reranker = None
        except Exception as e:
            st.sidebar.error(f"❌ Failed to load reranker: {str(e)}")
            reranker = None

    # Google Search configuration
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Web Search Options")
    use_web_search = st.sidebar.checkbox("Enable Web Search", value=False)

    search_tool = None
    augmented_rag = None
    if use_web_search:
        serpapi_key = st.sidebar.text_input(
            "SerpAPI Key",
            type="password",
            help="Get your API key from https://serpapi.com/"
        )

        if serpapi_key:
            try:
                search_tool = GoogleSearchTool(api_key=serpapi_key)
                augmented_rag = SearchAugmentedRAG(
                    vector_db=index,
                    search_tool=search_tool,
                    reranker=reranker
                )
                st.sidebar.success("✅ Web search enabled")
            except Exception as e:
                st.sidebar.error(f"❌ Failed to initialize web search: {str(e)}")
                search_tool = None
                augmented_rag = None
        else:
            st.sidebar.warning("⚠️ Enter SerpAPI key to enable web search")

    # Flash Attention configuration
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚡ Performance Options")

    flash_tester = FlashAttentionTester()
    flash_compatible, flash_message = check_flash_attention_compatibility()

    if flash_compatible:
        use_flash_attention = st.sidebar.checkbox(
            "Use Flash Attention (Future)",
            value=False,
            help="Flash Attention 2 for transformers models (not applicable to current LlamaCpp setup)"
        )
        st.sidebar.success(f"✅ {flash_message}")
        st.sidebar.info("Current LlamaCpp models have built-in optimizations")

    # Agent configuration
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🤖 Agent Mode")
    use_agent = st.sidebar.checkbox(
        "Enable Agent Mode",
        value=False,
        help="Use function calling agent for complex queries"
    )

    agent = None
    if use_agent:
        # Create tool registry with available tools
        tool_registry = create_default_tool_registry(
            vector_db=index,
            search_tool=search_tool if use_web_search else None
        )

        # Create agent
        agent = AgentConfig.create_agent(
            llm=llm,
            tool_registry=tool_registry,
            max_iterations=5
        )

        st.sidebar.success("✅ Agent mode enabled")
        st.sidebar.info(f"Available tools: {', '.join(tool_registry.get_available_tools())}")
    else:
        agent = None

    # Safety configuration
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🛡️ Safety Settings")
    enable_safety = st.sidebar.checkbox(
        "Enable Safety Guard",
        value=True,
        help="Check inputs and outputs for safety violations"
    )

    safety_guard = None
    if enable_safety:
        safety_backend = st.sidebar.selectbox(
            "Safety Backend",
            ["simple", "llama_guard"],
            help="Safety checking method"
        )

        try:
            safety_guard = SafetyConfig.create_guard(backend=safety_backend)
            if safety_guard.is_available():
                st.sidebar.success(f"✅ Safety guard active ({safety_backend})")
            else:
                st.sidebar.warning(f"⚠️ Safety guard not available")
        except Exception as e:
            st.sidebar.error(f"❌ Failed to initialize safety guard: {str(e)}")
            safety_guard = None

    # Long-term memory configuration
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧠 Long-term Memory")
    enable_memory = st.sidebar.checkbox(
        "Enable Memory",
        value=False,
        help="Store and retrieve long-term user preferences and conversation history"
    )

    memory_system = None
    memory_manager = None
    user_id = None

    if enable_memory:
        memory_backend = st.sidebar.selectbox(
            "Memory Backend",
            ["file", "mem0"],
            help="Where to store long-term memories"
        )

        if memory_backend == "mem0":
            mem0_key = st.sidebar.text_input(
                "Mem0 API Key",
                type="password",
                help="Get your API key from Mem0"
            )
            if mem0_key:
                memory_config = {"api_key": mem0_key}
            else:
                memory_config = {}
                st.sidebar.warning("⚠️ Mem0 requires API key")
        else:
            memory_config = {"storage_path": "user_memories"}

        try:
            memory_system = LongTermMemory(backend=memory_backend, backend_config=memory_config)
            memory_manager = MemoryManager(memory_system)

            # Simple user ID (in production, use proper user authentication)
            user_id = st.sidebar.text_input(
                "User ID",
                value="default_user",
                help="Identifier for storing/retrieving memories"
            )

            if memory_system.is_available():
                st.sidebar.success(f"✅ Memory system active ({memory_backend})")
            else:
                st.sidebar.warning(f"⚠️ Memory system not available")

        except Exception as e:
            st.sidebar.error(f"❌ Failed to initialize memory: {str(e)}")
            memory_system = None
            memory_manager = None

    # Multimodal configuration
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🖼️ Multimodal Support")
    enable_multimodal = st.sidebar.checkbox(
        "Enable Image Analysis",
        value=False,
        help="Analyze images and include them in conversations"
    )

    vision_client = None
    multimodal_rag = None

    if enable_multimodal:
        vision_model = st.sidebar.selectbox(
            "Vision Model",
            ["llava-hf/llava-1.5-7b-hf", "jinaai/jina-vlm"],
            help="Model for image analysis"
        )

        try:
            vision_client = VisionLLMClient(model_name=vision_model)
            multimodal_rag = MultimodalRAG(
                text_vector_db=index,
                vision_client=vision_client
            )

            if vision_client.is_available:
                st.sidebar.success(f"✅ Vision model loaded ({vision_model.split('/')[-1]})")
            else:
                st.sidebar.warning(f"⚠️ Vision model not available")

        except Exception as e:
            st.sidebar.error(f"❌ Failed to load vision model: {str(e)}")
            vision_client = None
            multimodal_rag = None

    # Image upload for multimodal conversations
    uploaded_image = None
    temp_image_path = None

    if enable_multimodal:
        st.markdown("### 📸 Image Upload")
        uploaded_file = st.file_uploader(
            "Upload an image to analyze",
            type=["jpg", "jpeg", "png", "bmp", "tiff", "webp"],
            help="Upload an image to include in your conversation"
        )

        if uploaded_file:
            if ImageProcessor.is_supported_image(uploaded_file.name):
                # Save uploaded image temporarily
                temp_image_path = ImageProcessor.save_uploaded_image(uploaded_file)

                # Display the image
                from PIL import Image
                image = Image.open(temp_image_path)
                st.image(image, caption="Uploaded Image", width=300)

                uploaded_image = temp_image_path

                # Auto-analyze option
                if st.button("🔍 Analyze Image"):
                    with st.spinner("Analyzing image..."):
                        if multimodal_rag:
                            analysis_result = multimodal_rag.process_image(temp_image_path)
                            if "error" not in analysis_result:
                                st.success("Image analyzed and added to knowledge base!")
                                st.write("**Description:**", analysis_result.get("description", ""))
                                if analysis_result.get("extracted_text"):
                                    st.write("**Extracted Text:**", analysis_result["extracted_text"])
                            else:
                                st.error(f"Analysis failed: {analysis_result['error']}")
            else:
                st.error("Unsupported image format")

    # Supervise user input
    if user_input := st.chat_input("Input your question!"):
        # Safety check for user input
        if safety_guard:
            is_safe, violation_msg = check_input_safety(safety_guard, user_input, role="user")
            if not is_safe:
                st.error(f"⚠️ {violation_msg}")
                st.stop()  # Stop processing this request

        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(user_input)

        # Display retrieved documents with content previews, and updates the chat interface with the assistant's
        # responses.
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            with st.spinner(
                text="Refining the question and Retrieving the docs – hang tight! This should take seconds."
            ):
                refined_user_input = refine_question(
                    llm, user_input, chat_history=chat_history, max_new_tokens=max_new_tokens
                )

                # Add memory context if available
                memory_context = ""
                if memory_manager and user_id:
                    memory_context = memory_manager.get_memory_context(user_id, refined_user_input)
                    if memory_context:
                        # Prepend memory context to the refined input
                        refined_user_input = f"{memory_context}\n\nCurrent query: {refined_user_input}"
                # Use multimodal retrieval if image is uploaded
                if uploaded_image and multimodal_rag:
                    with st.spinner("Searching with image analysis..."):
                        retrieved_contents, sources = multimodal_rag.search_with_image(
                            query=refined_user_input,
                            image_path=uploaded_image,
                            k=parameters.k
                        )
                # Use augmented retrieval if web search is enabled
                elif augmented_rag:
                    with st.spinner("Searching local knowledge base and web..."):
                        retrieved_contents, sources = augmented_rag.retrieve_augmented(
                            query=refined_user_input,
                            local_k=parameters.k // 2 if reranker else parameters.k,
                            web_k=parameters.k // 2 if reranker else min(3, parameters.k),
                            combine_results=True
                        )
                else:
                    retrieved_contents, sources = index.similarity_search_with_threshold(
                        query=refined_user_input, k=parameters.k
                    )

                # Apply reranking if enabled (for local-only or when not using augmented RAG)
                if reranker and retrieved_contents and not augmented_rag:
                    with st.spinner("Reranking documents for better relevance..."):
                        # Get more documents for reranking (typically 2-3x the final count)
                        expanded_k = min(parameters.k * 3, 20)  # Cap at 20 to avoid too many docs
                        expanded_contents, _ = index.similarity_search_with_threshold(
                            query=refined_user_input, k=expanded_k
                        )

                        # Rerank the expanded set
                        reranked_contents = reranker.rerank(
                            query=refined_user_input,
                            documents=expanded_contents,
                            top_k=parameters.k
                        )

                        # Update retrieved contents with reranked results
                        retrieved_contents = reranked_contents

                        # Update sources with reranking information
                        sources = []
                        for doc in retrieved_contents:
                            rerank_score = doc.metadata.get('rerank_score', 0.0)
                            sources.append({
                                "score": round(rerank_score, 3),
                                "document": doc.metadata.get("source"),
                                "content_preview": f"{doc.page_content[0:256]}...",
                                "reranked": True
                            })
                if retrieved_contents:
                    full_response += "Here are the retrieved text chunks with a content preview: \n\n"
                    message_placeholder.markdown(full_response)

                    for source in sources:
                        full_response += prettify_source(source)
                        full_response += "\n\n"
                        message_placeholder.markdown(full_response)

                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                    full_response += "I did not detect any pertinent chunk of text from the documents. \n\n"
                    message_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

        # Display assistant response in chat message container
        start_time = time.time()
        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            if agent:
                # Use agent for response generation
                with st.spinner(text="Agent is working on your query – using tools as needed..."):
                    # Convert chat history to agent format
                    agent_history = []
                    for msg in chat_history.messages[-4:]:  # Last 4 exchanges
                        if "question:" in msg:
                            question = msg.split("question: ", 1)[1].split(", answer:")[0]
                            agent_history.append({"role": "user", "content": question})
                        elif "answer:" in msg:
                            answer = msg.split("answer: ", 1)[1]
                            agent_history.append({"role": "assistant", "content": answer})

                    # Get agent response
                    answer = agent.run(user_input, agent_history)

                    message_placeholder.markdown(answer)
                    full_response = answer

            else:
                # Use standard RAG pipeline
                full_response = ""
                with st.spinner(text="Refining the context and Generating the answer for each text chunk – hang tight! "):
                    streamer, _ = answer_with_context(
                        llm, ctx_synthesis_strategy, user_input, chat_history, retrieved_contents, max_new_tokens
                    )
                    for token in streamer:
                        full_response += llm.parse_token(token)
                        message_placeholder.markdown(full_response + "▌")

                    if llm.model_settings.reasoning:
                        answer = extract_content_after_reasoning(full_response, llm.model_settings.reasoning_stop_tag)
                        if answer == "":
                            answer = "I wasn't able to provide the answer; Do you want me to try again?"
                    else:
                        answer = full_response

                    message_placeholder.markdown(answer)

            # Safety check for generated response
            if safety_guard:
                is_safe, violation_msg = check_output_safety(safety_guard, answer)
                if not is_safe:
                    safe_response = "I cannot provide that information as it may contain unsafe content."
                    message_placeholder.markdown(safe_response)
                    answer = safe_response

            # Update chat history
            chat_history.append(f"question: {user_input}, answer: {answer}")

            # Store conversation memory if enabled
            if memory_manager and user_id:
                try:
                    memory_manager.add_conversation_memory(
                        user_id=user_id,
                        question=user_input,
                        answer=answer,
                        importance_threshold=0.6
                    )
                except Exception as e:
                    logger.error(f"Error storing conversation memory: {e}")

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": answer})

        # Cleanup temporary image file
        if temp_image_path:
            try:
                ImageProcessor.cleanup_temp_image(temp_image_path)
            except Exception as e:
                logger.error(f"Error cleaning up image: {e}")

        took = time.time() - start_time
        logger.info(f"\n--- Took {took:.2f} seconds ---")


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RAG Chatbot")

    model_list = get_models()
    default_model = model_list[0]

    synthesis_strategy_list = get_ctx_synthesis_strategies()
    default_synthesis_strategy = synthesis_strategy_list[0]

    parser.add_argument(
        "--model",
        type=str,
        choices=model_list,
        help=f"Model to be used. Defaults to {default_model}.",
        required=False,
        const=default_model,
        nargs="?",
        default=default_model,
    )

    parser.add_argument(
        "--synthesis-strategy",
        type=str,
        choices=synthesis_strategy_list,
        help=f"Model to be used. Defaults to {default_synthesis_strategy}.",
        required=False,
        const=default_synthesis_strategy,
        nargs="?",
        default=default_synthesis_strategy,
    )

    parser.add_argument(
        "--k",
        type=int,
        help="Number of chunks to return from the similarity search. Defaults to 2.",
        required=False,
        default=2,
    )

    parser.add_argument(
        "--max-new-tokens",
        type=int,
        help="The maximum number of tokens to generate in the answer. Defaults to 512.",
        required=False,
        default=512,
    )

    return parser.parse_args()


# streamlit run rag_chatbot_app.py
if __name__ == "__main__":
    try:
        args = get_args()
        main(args)
    except Exception as error:
        logger.error(f"An error occurred: {str(error)}", exc_info=True, stack_info=True)
        sys.exit(1)
