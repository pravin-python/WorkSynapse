"""
WorkSynapse Base Command
========================
Base class for all management commands with professional logging,
database session handling, and transaction management.

Features:
- Structured logging with Rich output
- Database session lifecycle management
- Transaction-safe operations with automatic rollback
- Formatted console output
- Error handling and reporting
"""

import logging
import asyncio
import sys
from abc import ABC, abstractmethod
from typing import Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database.session import engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler()]
)


class CommandOutput:
    """
    Helper class for formatted console output.
    Provides consistent styling for CLI commands.
    """
    
    # ANSI Color Codes
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    @staticmethod
    def success(message: str) -> None:
        """Print success message with green checkmark."""
        print(f"{CommandOutput.GREEN}✅ {message}{CommandOutput.ENDC}")
    
    @staticmethod
    def error(message: str) -> None:
        """Print error message with red X."""
        print(f"{CommandOutput.FAIL}❌ {message}{CommandOutput.ENDC}")
    
    @staticmethod
    def warning(message: str) -> None:
        """Print warning message with yellow triangle."""
        print(f"{CommandOutput.WARNING}⚠️  {message}{CommandOutput.ENDC}")
    
    @staticmethod
    def info(message: str) -> None:
        """Print info message with blue circle."""
        print(f"{CommandOutput.BLUE}ℹ️  {message}{CommandOutput.ENDC}")
    
    @staticmethod
    def header(title: str) -> None:
        """Print a styled header."""
        border = "═" * (len(title) + 4)
        print(f"\n{CommandOutput.BOLD}{CommandOutput.CYAN}╔{border}╗")
        print(f"║  {title}  ║")
        print(f"╚{border}╝{CommandOutput.ENDC}\n")
    
    @staticmethod
    def table_row(label: str, value: str, width: int = 30) -> None:
        """Print a table row with label and value."""
        print(f"  {CommandOutput.BOLD}{label:<{width}}{CommandOutput.ENDC}: {value}")
    
    @staticmethod
    def divider() -> None:
        """Print a divider line."""
        print(f"{CommandOutput.CYAN}{'─' * 60}{CommandOutput.ENDC}")
    
    @staticmethod
    def bullet(message: str) -> None:
        """Print a bullet point."""
        print(f"  • {message}")


class BaseCommand(ABC):
    """
    Base class for all WorkSynapse management commands.
    
    Features:
    - Async database session management
    - Automatic transaction handling
    - Structured logging
    - Error recovery with rollback
    - Formatted output helpers
    
    Subclasses must implement:
    - execute(db, *args, **kwargs): Main command logic
    
    Optional overrides:
    - validate(*args, **kwargs): Pre-execution validation
    - cleanup(db): Post-execution cleanup
    
    Usage:
        class MyCommand(BaseCommand):
            async def execute(self, db, **kwargs):
                # Your command logic here
                pass
        
        cmd = MyCommand()
        cmd.run(arg1=value1, arg2=value2)
    """
    
    # Command metadata (override in subclasses)
    name: str = "base"
    description: str = "Base command"
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.output = CommandOutput()
        self.async_session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        self._start_time: Optional[datetime] = None
    
    @abstractmethod
    async def execute(self, db: AsyncSession, *args, **kwargs) -> Any:
        """
        Main execution method to be implemented by subclasses.
        
        Args:
            db: Database session (automatically provided)
            *args, **kwargs: Command-specific arguments
        
        Returns:
            Any result from the command execution
        
        Raises:
            Any exception will trigger automatic rollback
        """
        raise NotImplementedError("Subclasses must implement execute()")
    
    async def validate(self, *args, **kwargs) -> bool:
        """
        Optional validation before execution.
        
        Override this method to add pre-execution validation.
        Return False to abort execution.
        
        Returns:
            bool: True if validation passes, False to abort
        """
        return True
    
    async def cleanup(self, db: AsyncSession) -> None:
        """
        Optional cleanup after execution.
        
        Override this method to add post-execution cleanup.
        Called after successful execution (not on error).
        """
        pass
    
    @asynccontextmanager
    async def get_session(self):
        """
        Context manager for database session with automatic transaction handling.
        
        Provides:
        - Automatic commit on success
        - Automatic rollback on error
        - Proper session cleanup
        """
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def run_async(self, *args, **kwargs) -> Any:
        """
        Async wrapper for command execution with full lifecycle management.
        
        Lifecycle:
        1. Validation
        2. Session creation
        3. Execution
        4. Cleanup (on success)
        5. Commit/Rollback
        6. Session close
        """
        self._start_time = datetime.now()
        
        # Validation phase
        if not await self.validate(*args, **kwargs):
            self.output.error("Validation failed. Command aborted.")
            return None
        
        self.logger.info(f"Starting {self.__class__.__name__}...")
        
        # Execution phase
        async with self.get_session() as db:
            try:
                result = await self.execute(db, *args, **kwargs)
                await self.cleanup(db)
                
                elapsed = (datetime.now() - self._start_time).total_seconds()
                self.logger.info(f"Command completed in {elapsed:.2f}s")
                
                return result
                
            except Exception as e:
                self.logger.error(f"Command failed: {e}", exc_info=True)
                self.output.error(f"Command failed: {str(e)}")
                raise
    
    def run(self, *args, **kwargs) -> Any:
        """
        Synchronous entry point for CLI execution.
        
        Handles:
        - Event loop setup for Windows
        - Keyboard interrupt handling
        - Exit code management
        """
        # Windows-specific event loop policy
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        try:
            return asyncio.run(self.run_async(*args, **kwargs))
        except KeyboardInterrupt:
            self.output.warning("Command cancelled by user.")
            sys.exit(130)  # Standard interrupt exit code
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            sys.exit(1)
    
    def log_secure(self, message: str, **kwargs) -> None:
        """
        Log a message with sensitive data redaction.
        
        Use this for logging that might contain passwords or tokens.
        Automatically redacts values for keys containing sensitive terms.
        """
        sensitive_keys = {'password', 'secret', 'token', 'key', 'auth'}
        
        safe_kwargs = {}
        for key, value in kwargs.items():
            if any(s in key.lower() for s in sensitive_keys):
                safe_kwargs[key] = '***REDACTED***'
            else:
                safe_kwargs[key] = value
        
        self.logger.info(f"{message} | {safe_kwargs}")
