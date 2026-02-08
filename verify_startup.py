
import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    print("Attempting to import app.main...")
    from app.main import app
    print("Successfully imported app.main")
    
    print("Attempting to import RAG components...")
    from app.ai.rag.rag_service import get_rag_service
    from app.worker.tasks.rag import process_rag_document
    from app.api.v1.routers import rag
    print("Successfully imported RAG components")
    
    print("Startup verification passed!")
except Exception as e:
    print(f"Startup verification FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
