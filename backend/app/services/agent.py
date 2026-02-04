"""
WorkSynapse Agent Service
=========================
AI Agent governance service with complete audit logging.

Features:
- Agent lifecycle management
- Session management
- Token/cost tracking
- Action logging
- Permission verification
"""
from typing import Any, Dict, List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.agent.model import (
    Agent, AgentStatus, AgentType, LLMProvider,
    AgentSession, AgentSessionStatus,
    AgentMessage, AgentCall, AgentCallStatus,
    AgentAction, AgentActionType, AgentActionStatus,
    AgentCostLog, AgentTask, AgentTool
)
from app.models.user.model import User
from app.services.base import SecureCRUDBase, NotFoundError, PermissionError, ValidationError
from pydantic import BaseModel, field_validator
import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# TOKEN PRICING (USD per 1K tokens)
# =============================================================================

TOKEN_PRICING = {
    "gpt-4": {"prompt": 0.03, "completion": 0.06},
    "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
    "gpt-4o": {"prompt": 0.005, "completion": 0.015},
    "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
    "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
    "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
    "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
    "claude-3.5-sonnet": {"prompt": 0.003, "completion": 0.015},
    "claude-3-haiku": {"prompt": 0.00025, "completion": 0.00125},
    "gemini-pro": {"prompt": 0.00025, "completion": 0.0005},
    "gemini-1.5-pro": {"prompt": 0.00125, "completion": 0.005},
    "gemini-1.5-flash": {"prompt": 0.000075, "completion": 0.0003},
}


# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class AgentCreate(BaseModel):
    """Schema for creating an agent."""
    name: str
    slug: str
    description: Optional[str] = None
    agent_type: AgentType = AgentType.CUSTOM
    llm_provider: LLMProvider = LLMProvider.OPENAI
    llm_model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: str
    goals: Optional[List[str]] = None
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v: str) -> str:
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must be lowercase alphanumeric with hyphens only')
        if len(v) < 3 or len(v) > 100:
            raise ValueError('Slug must be between 3 and 100 characters')
        return v
    
    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if v < 0 or v > 2:
            raise ValueError('Temperature must be between 0 and 2')
        return v


class AgentUpdate(BaseModel):
    """Schema for updating an agent."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[AgentStatus] = None
    llm_model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    goals: Optional[List[str]] = None


class AgentMessageCreate(BaseModel):
    """Schema for creating an agent message."""
    role: str
    content: str
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args: Optional[dict] = None
    tool_result: Optional[dict] = None


# =============================================================================
# AGENT SERVICE
# =============================================================================

class AgentService(SecureCRUDBase[Agent, AgentCreate, AgentUpdate]):
    """
    AI Agent governance service.
    
    Provides:
    - Agent CRUD with permission checks
    - Session management
    - Complete audit trail
    - Token & cost tracking
    """
    
    def __init__(self):
        super().__init__(Agent, enable_soft_delete=True, enable_audit_log=True)
    
    # =========================================================================
    # AGENT OPERATIONS
    # =========================================================================
    
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: AgentCreate,
        created_by_user_id: int,
        commit: bool = True,
    ) -> Agent:
        """Create a new agent."""
        # Check for existing slug
        existing = await self.get_by_slug(db, obj_in.slug)
        if existing:
            raise ValidationError(f"Agent with slug '{obj_in.slug}' already exists")
        
        agent_data = obj_in.model_dump()
        agent_data['created_by_user_id'] = created_by_user_id
        
        db_obj = Agent(**agent_data)
        db.add(db_obj)
        
        if commit:
            await db.commit()
            await db.refresh(db_obj)
        
        logger.info(f"Created agent {db_obj.name} (id={db_obj.id}) by user {created_by_user_id}")
        return db_obj
    
    async def get_by_slug(
        self,
        db: AsyncSession,
        slug: str,
    ) -> Optional[Agent]:
        """Get agent by slug."""
        query = select(Agent).filter(Agent.slug == slug, Agent.is_deleted == False)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_active_agents(
        self,
        db: AsyncSession,
        *,
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> List[Agent]:
        """Get all active agents, optionally filtered by access."""
        query = select(Agent).filter(
            Agent.status == AgentStatus.ACTIVE,
            Agent.is_deleted == False
        )
        
        if project_id:
            query = query.filter(
                (Agent.project_id == project_id) | (Agent.project_id.is_(None))
            )
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def can_user_access_agent(
        self,
        db: AsyncSession,
        agent: Agent,
        user: User,
    ) -> bool:
        """Check if user can access an agent."""
        # Superusers can access all agents
        if user.is_superuser:
            return True
        
        # Creator can always access
        if agent.created_by_user_id == user.id:
            return True
        
        # Public agents are accessible to all
        if agent.is_public:
            return True
        
        # Check user-specific permissions
        from app.models.agent.model import AgentUserPermission
        query = select(AgentUserPermission).filter(
            AgentUserPermission.agent_id == agent.id,
            AgentUserPermission.user_id == user.id,
            AgentUserPermission.can_use == True
        )
        result = await db.execute(query)
        user_perm = result.scalars().first()
        if user_perm:
            return True
        
        # Check role-based permissions
        for role in user.roles:
            if role in agent.role_permissions:
                return True
        
        return False
    
    # =========================================================================
    # SESSION OPERATIONS
    # =========================================================================
    
    async def create_session(
        self,
        db: AsyncSession,
        *,
        agent_id: int,
        user_id: int,
        context_project_id: Optional[int] = None,
        context_task_id: Optional[int] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AgentSession:
        """Create a new agent session."""
        agent = await self.get_or_404(db, agent_id)
        
        session = AgentSession(
            session_uuid=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            status=AgentSessionStatus.ACTIVE,
            context_project_id=context_project_id,
            context_task_id=context_task_id,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        
        db.add(session)
        
        # Update agent stats
        agent.total_sessions += 1
        agent.last_used_at = datetime.datetime.now(datetime.timezone.utc)
        
        await db.commit()
        await db.refresh(session)
        
        logger.info(f"Created session {session.session_uuid} for agent {agent_id} by user {user_id}")
        return session
    
    async def get_session(
        self,
        db: AsyncSession,
        session_uuid: str,
    ) -> Optional[AgentSession]:
        """Get session by UUID."""
        query = select(AgentSession).filter(AgentSession.session_uuid == session_uuid)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def end_session(
        self,
        db: AsyncSession,
        session: AgentSession,
    ):
        """End an agent session."""
        session.status = AgentSessionStatus.ENDED
        session.ended_at = datetime.datetime.now(datetime.timezone.utc)
        await db.commit()
    
    async def get_user_sessions(
        self,
        db: AsyncSession,
        user_id: int,
        *,
        agent_id: Optional[int] = None,
        active_only: bool = False,
        limit: int = 50,
    ) -> List[AgentSession]:
        """Get sessions for a user."""
        query = select(AgentSession).filter(AgentSession.user_id == user_id)
        
        if agent_id:
            query = query.filter(AgentSession.agent_id == agent_id)
        
        if active_only:
            query = query.filter(AgentSession.status == AgentSessionStatus.ACTIVE)
        
        query = query.order_by(AgentSession.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    # =========================================================================
    # MESSAGE OPERATIONS
    # =========================================================================
    
    async def add_message(
        self,
        db: AsyncSession,
        *,
        session: AgentSession,
        role: str,
        content: str,
        tokens_prompt: int = 0,
        tokens_completion: int = 0,
        tool_call_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_args: Optional[dict] = None,
        tool_result: Optional[dict] = None,
        processing_time_ms: Optional[int] = None,
    ) -> AgentMessage:
        """Add a message to a session."""
        message = AgentMessage(
            session_id=session.id,
            role=role,
            content=content,
            tokens_prompt=tokens_prompt,
            tokens_completion=tokens_completion,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            tool_args=tool_args,
            tool_result=tool_result,
            processing_time_ms=processing_time_ms,
        )
        
        db.add(message)
        
        # Update session stats
        session.message_count += 1
        session.total_tokens_used += tokens_prompt + tokens_completion
        session.last_activity_at = datetime.datetime.now(datetime.timezone.utc)
        
        await db.commit()
        await db.refresh(message)
        
        return message
    
    async def get_session_messages(
        self,
        db: AsyncSession,
        session_id: int,
        *,
        limit: int = 100,
    ) -> List[AgentMessage]:
        """Get messages for a session."""
        query = select(AgentMessage).filter(
            AgentMessage.session_id == session_id
        ).order_by(AgentMessage.created_at).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    # =========================================================================
    # LLM CALL LOGGING
    # =========================================================================
    
    async def log_llm_call(
        self,
        db: AsyncSession,
        *,
        session: AgentSession,
        agent: Agent,
        user_id: int,
        prompt_messages: List[dict],
        prompt_tokens: int,
        llm_model: str,
        temperature: float,
        max_tokens_requested: int,
        request_ip: Optional[str] = None,
    ) -> AgentCall:
        """
        Log the start of an LLM API call.
        
        CRITICAL: This creates an audit record before the call is made.
        """
        call = AgentCall(
            call_uuid=str(uuid.uuid4()),
            session_id=session.id,
            agent_id=agent.id,
            user_id=user_id,
            llm_provider=agent.llm_provider.value,
            llm_model=llm_model,
            temperature=temperature,
            max_tokens_requested=max_tokens_requested,
            status=AgentCallStatus.PENDING,
            prompt_messages=prompt_messages,
            prompt_tokens=prompt_tokens,
            request_ip=request_ip,
        )
        
        db.add(call)
        await db.commit()
        await db.refresh(call)
        
        return call
    
    async def complete_llm_call(
        self,
        db: AsyncSession,
        call: AgentCall,
        *,
        response_content: Optional[str] = None,
        response_tool_calls: Optional[list] = None,
        completion_tokens: int,
        status: AgentCallStatus = AgentCallStatus.COMPLETED,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None,
    ):
        """
        Complete an LLM call log with response data.
        
        CRITICAL: Records the full response for audit.
        """
        call.status = status
        call.response_content = response_content
        call.response_tool_calls = response_tool_calls
        call.completion_tokens = completion_tokens
        call.total_tokens = call.prompt_tokens + completion_tokens
        call.completed_at = datetime.datetime.now(datetime.timezone.utc)
        call.error_message = error_message
        call.error_code = error_code
        
        # Calculate latency
        if call.started_at:
            delta = call.completed_at - call.started_at
            call.latency_ms = int(delta.total_seconds() * 1000)
        
        # Calculate cost
        call.cost_usd = self.calculate_cost(
            call.llm_model,
            call.prompt_tokens,
            completion_tokens
        )
        
        # Update session totals
        session = await db.get(AgentSession, call.session_id)
        if session:
            session.total_tokens_used += call.total_tokens
            session.total_cost_usd += call.cost_usd
        
        # Update agent totals
        agent = await db.get(Agent, call.agent_id)
        if agent:
            agent.total_tokens_used += call.total_tokens
            agent.total_cost_usd += call.cost_usd
            agent.total_messages += 1
        
        await db.commit()
        
        # Log cost
        await self._log_daily_cost(
            db,
            agent_id=call.agent_id,
            user_id=call.user_id,
            llm_provider=call.llm_provider,
            llm_model=call.llm_model,
            prompt_tokens=call.prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=call.cost_usd,
        )
        
        logger.info(
            f"LLM call {call.call_uuid} completed: "
            f"{call.total_tokens} tokens, ${call.cost_usd:.6f}"
        )
    
    def calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """Calculate cost for an LLM call."""
        pricing = TOKEN_PRICING.get(model, {"prompt": 0.01, "completion": 0.03})
        
        prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (completion_tokens / 1000) * pricing["completion"]
        
        return prompt_cost + completion_cost
    
    async def _log_daily_cost(
        self,
        db: AsyncSession,
        *,
        agent_id: int,
        user_id: int,
        llm_provider: str,
        llm_model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
    ):
        """Log daily cost aggregation."""
        today = datetime.date.today()
        pricing = TOKEN_PRICING.get(llm_model, {"prompt": 0.01, "completion": 0.03})
        
        # Check for existing record
        query = select(AgentCostLog).filter(
            AgentCostLog.agent_id == agent_id,
            AgentCostLog.user_id == user_id,
            AgentCostLog.log_date == today,
            AgentCostLog.llm_model == llm_model,
        )
        result = await db.execute(query)
        cost_log = result.scalars().first()
        
        if cost_log:
            # Update existing
            cost_log.prompt_tokens += prompt_tokens
            cost_log.completion_tokens += completion_tokens
            cost_log.total_tokens += prompt_tokens + completion_tokens
            cost_log.prompt_cost_usd += (prompt_tokens / 1000) * pricing["prompt"]
            cost_log.completion_cost_usd += (completion_tokens / 1000) * pricing["completion"]
            cost_log.total_cost_usd += cost_usd
            cost_log.request_count += 1
        else:
            # Create new
            cost_log = AgentCostLog(
                agent_id=agent_id,
                user_id=user_id,
                log_date=today,
                llm_provider=llm_provider,
                llm_model=llm_model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                prompt_cost_usd=(prompt_tokens / 1000) * pricing["prompt"],
                completion_cost_usd=(completion_tokens / 1000) * pricing["completion"],
                total_cost_usd=cost_usd,
                request_count=1,
                price_per_1k_prompt_tokens=pricing["prompt"],
                price_per_1k_completion_tokens=pricing["completion"],
            )
            db.add(cost_log)
        
        await db.commit()
    
    # =========================================================================
    # ACTION LOGGING
    # =========================================================================
    
    async def log_action(
        self,
        db: AsyncSession,
        *,
        session: AgentSession,
        action_type: AgentActionType,
        call_id: Optional[int] = None,
        tool_id: Optional[int] = None,
        tool_name: Optional[str] = None,
        input_params: Optional[dict] = None,
        requires_approval: bool = False,
    ) -> AgentAction:
        """
        Log an agent action.
        
        CRITICAL: All agent actions are tracked for audit.
        """
        action = AgentAction(
            action_uuid=str(uuid.uuid4()),
            session_id=session.id,
            call_id=call_id,
            action_type=action_type,
            tool_id=tool_id,
            tool_name=tool_name,
            status=AgentActionStatus.PENDING if requires_approval else AgentActionStatus.EXECUTING,
            input_params=input_params,
            requires_approval=requires_approval,
        )
        
        db.add(action)
        await db.commit()
        await db.refresh(action)
        
        logger.info(f"Logged action {action.action_uuid}: {action_type.value}")
        return action
    
    async def complete_action(
        self,
        db: AsyncSession,
        action: AgentAction,
        *,
        status: AgentActionStatus,
        output_result: Optional[dict] = None,
        error_message: Optional[str] = None,
        affected_resource_type: Optional[str] = None,
        affected_resource_id: Optional[int] = None,
    ):
        """Complete an action log."""
        action.status = status
        action.output_result = output_result
        action.error_message = error_message
        action.affected_resource_type = affected_resource_type
        action.affected_resource_id = affected_resource_id
        action.completed_at = datetime.datetime.now(datetime.timezone.utc)
        
        if action.started_at:
            delta = action.completed_at - action.started_at
            action.execution_time_ms = int(delta.total_seconds() * 1000)
        
        await db.commit()
    
    # =========================================================================
    # COST ANALYTICS
    # =========================================================================
    
    async def get_user_cost_summary(
        self,
        db: AsyncSession,
        user_id: int,
        *,
        start_date: Optional[datetime.date] = None,
        end_date: Optional[datetime.date] = None,
    ) -> Dict[str, Any]:
        """Get cost summary for a user."""
        query = select(
            func.sum(AgentCostLog.total_tokens).label("total_tokens"),
            func.sum(AgentCostLog.total_cost_usd).label("total_cost"),
            func.sum(AgentCostLog.request_count).label("total_requests"),
        ).filter(AgentCostLog.user_id == user_id)
        
        if start_date:
            query = query.filter(AgentCostLog.log_date >= start_date)
        if end_date:
            query = query.filter(AgentCostLog.log_date <= end_date)
        
        result = await db.execute(query)
        row = result.first()
        
        return {
            "total_tokens": row.total_tokens or 0,
            "total_cost_usd": float(row.total_cost or 0),
            "total_requests": row.total_requests or 0,
        }
    
    async def get_agent_usage_stats(
        self,
        db: AsyncSession,
        agent_id: int,
    ) -> Dict[str, Any]:
        """Get usage statistics for an agent."""
        agent = await self.get_or_404(db, agent_id)
        
        # Get session count
        session_query = select(func.count(AgentSession.id)).filter(
            AgentSession.agent_id == agent_id
        )
        session_result = await db.execute(session_query)
        session_count = session_result.scalar_one()
        
        # Get unique user count
        user_query = select(func.count(func.distinct(AgentSession.user_id))).filter(
            AgentSession.agent_id == agent_id
        )
        user_result = await db.execute(user_query)
        unique_users = user_result.scalar_one()
        
        return {
            "agent_id": agent_id,
            "name": agent.name,
            "total_sessions": session_count,
            "total_messages": agent.total_messages,
            "total_tokens_used": agent.total_tokens_used,
            "total_cost_usd": agent.total_cost_usd,
            "unique_users": unique_users,
            "last_used_at": agent.last_used_at,
        }


# Singleton instance
agent_service = AgentService()
