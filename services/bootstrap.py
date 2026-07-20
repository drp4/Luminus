from services.database import get_session, get_session_ctx, init_db, seed_defaults
from services.runtime.kernel import AgentRuntime
from services.runtime.events import EventBus
from services.runtime.guardrails import Guardrails
from services.runtime.loops import LoopScheduler
from services.profile.repository import ChildRepo, PersonaRepo, ProfileRepo
from services.memory.store import MemoryStore
from services.memory.profile_engine import ProfileEngine
from services.agent.agents.memory_agent import MemoryAgent
from services.gateway.routes.chat import init_runtime


async def bootstrap() -> AgentRuntime:
    """Initialize the full AOS stack and return the Runtime.

    Call once at application startup.
    """
    event_bus = EventBus()
    guard = Guardrails()
    profile_engine = ProfileEngine()

    # Wire Event Bus → Loop Scheduler
    loop_scheduler = LoopScheduler(event_bus=event_bus)
    loop_scheduler.wire()

    # Runtime starts without DB-dependent components
    # They will be injected on each request via session
    runtime = AgentRuntime(
        child_repo=None,  # Injected per-request
        persona_repo=None,
        profile_repo=None,
        profile_engine=profile_engine,
        memory_agent=None,
        event_bus=event_bus,
        guard=guard,
    )

    # Register runtime globally for FastAPI routes
    init_runtime(runtime)

    return runtime
