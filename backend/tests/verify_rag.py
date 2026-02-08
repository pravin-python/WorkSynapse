"""
Verification Script for RAG System
==================================

Tests the core components of the RAG system:
1. Retrieval (Mock/Real)
2. Prompt Assembly in Orchestrator
"""

import asyncio
import sys
import os

# Add project root to path
# Adjusted path to ensure 'app' is found (c:\Users\Admin\OneDrive\Desktop\Python\dream\WorkSynapse\backend)
sys.path.append("c:\\Users\\Admin\\OneDrive\\Desktop\\Python\\dream\\WorkSynapse\\backend")

# Mock database and dependencies
from unittest.mock import MagicMock, AsyncMock

async def test_components():
    print("🚀 Starting RAG System Verification...\n")

    # 1. Test Prompt Assembly
    print("Testing Prompt Assembly...")
    from app.agents.orchestrator.core import AgentOrchestrator
    
    # Mock dependencies
    orchestrator = AgentOrchestrator(
        config=MagicMock(),
        llm_router=MagicMock(),
        tool_registry=MagicMock(),
        memory_manager=MagicMock(),
        security_guard=MagicMock()
    )
    
    # Mock RAG Service
    mock_rag = AsyncMock()
    mock_rag.retrieve_context.return_value = ["Chunk 1: WorkSynapse uses FastAPI.", "Chunk 2: The database is PostgreSQL."]
    
    # Patch get_rag_service to return our mock
    from unittest.mock import patch
    
    # We need to patch where it is DEFINED because it is imported inside the function
    # OR patch where it is used if we can intercept the import.
    # Since it is imported inside _build_structured_system_prompt using 'from app.ai.rag.rag_service import get_rag_service',
    # we can patch 'app.ai.rag.rag_service.get_rag_service'.
    
    # However, since we can't context manager around the await call easily without changing structure,
    # we will use patch().start() and stop() or just patch the module after import if possible.
    # Simplest: use patch context manager for the call.
    
    # Mock Memory
    orchestrator.memory_manager.get_session_memory.return_value.get_all.return_value = {"last_topic": "deployment"}

    agent_config = {
        "id": 1,
        "system_prompt": "You are a bot.",
        "prompt_template": {
            "system_prompt": "You are a VERIFIED bot.",
            "goal_prompt": "Verify the system.",
            "instruction_prompt": "Run tests.",
            "output_prompt": "Return status code."
        }
    }

    message = "How does WorkSynapse backend work?"
    thread_id = "test-thread"

    with patch('app.ai.rag.rag_service.get_rag_service', return_value=mock_rag):
        prompt = await orchestrator._build_structured_system_prompt(agent_config, thread_id, message)
    
    print("\n--- ASSEMBLED PROMPT ---")
    print(prompt)
    print("------------------------\n")

    # Assertions
    assert "You are a VERIFIED bot." in prompt
    assert "Verify the system." in prompt
    assert "Chunk 1: WorkSynapse uses FastAPI." in prompt
    assert "last_topic: deployment" in prompt
    
    print("✅ Prompt Assembly Verified!\n")

    # 2. Test RAG Service Logic
    print("Testing RAG Service Logic...")
    from app.ai.rag.rag_service import RAGService
    
    rag = RAGService()
    rag.retriever.retrieve = AsyncMock(return_value=[{"content": "Real-time collaboration is key."}])
    
    results = await rag.retrieve_context("collaboration", k=1)
    # Note: retrieve_context returns List[str]
    # But my mock above returned list of dicts which is what retrieval_with_metadata returns.
    # retrieve returns List[str]. Let's fix mock for retrieve.
    rag.retriever.retrieve = AsyncMock(return_value=["Real-time collaboration is key."])
    results = await rag.retrieve_context("collaboration", k=1)

    assert len(results) == 1
    assert results[0] == "Real-time collaboration is key."
    print("✅ RAG Service Retrieval Verified!")

if __name__ == "__main__":
    asyncio.run(test_components())
