"""Crew orchestration — sequential and hierarchical modes."""

import time
from typing import Any

from crewai import Crew, Task
from langchain_core.language_models import BaseChatModel

from src.agents.definitions import create_agent
from src.models import AgentEvent, AgentRole, CrewMode, EventType, TaskRequest


class CrewOrchestrator:
    """Orchestrates a crew of agents to complete tasks."""

    def __init__(self, llm: BaseChatModel, verbose: bool = True) -> None:
        self.llm = llm
        self.verbose = verbose

    async def run(
        self,
        request: TaskRequest,
        event_callback: Any = None,
    ) -> dict[str, Any]:
        """Run a crew on the given task request."""
        start = time.time()

        # Create agents
        agents = [create_agent(role, self.llm) for role in request.agents]

        # Create tasks for each agent
        tasks = self._create_tasks(request, agents)

        # Build crew
        crew = Crew(
            agents=agents,
            tasks=tasks,
            verbose=self.verbose,
            process="sequential" if request.crew_mode == CrewMode.SEQUENTIAL else "hierarchical",
        )

        # Emit start event
        if event_callback:
            await event_callback(
                AgentEvent(
                    type=EventType.TASK_STARTED,
                    task_id="",
                    content=f"Crew started in {request.crew_mode.value} mode with {len(agents)} agents",
                )
            )

        # Execute crew
        try:
            # Emit agent-level events
            agent_outputs: dict[str, str] = {}
            for i, (agent, task) in enumerate(zip(agents, tasks)):
                role = request.agents[i]

                if event_callback:
                    await event_callback(
                        AgentEvent(
                            type=EventType.AGENT_THINKING,
                            task_id="",
                            agent=role,
                            content=f"{agent.role} is working on: {task.description[:100]}...",
                        )
                    )

            # Run the crew (blocking call)
            result = crew.kickoff()

            # Collect outputs
            for i, task in enumerate(tasks):
                role = request.agents[i]
                output = task.output.raw if task.output else "No output"
                agent_outputs[role.value] = output

                if event_callback:
                    await event_callback(
                        AgentEvent(
                            type=EventType.AGENT_RESULT,
                            task_id="",
                            agent=role,
                            content=output[:500],
                        )
                    )

            elapsed = (time.time() - start) * 1000

            return {
                "result": str(result),
                "agent_outputs": agent_outputs,
                "iterations": len(tasks),
                "latency_ms": elapsed,
            }

        except Exception as e:
            if event_callback:
                await event_callback(
                    AgentEvent(
                        type=EventType.TASK_FAILED,
                        task_id="",
                        content=str(e),
                    )
                )
            raise

    def _create_tasks(self, request: TaskRequest, agents: list) -> list[Task]:
        """Create CrewAI tasks for each agent based on their role."""
        tasks = []
        context_str = f"\nAdditional context: {request.context}" if request.context else ""

        for i, role in enumerate(request.agents):
            if role == AgentRole.RESEARCHER:
                tasks.append(
                    Task(
                        description=(
                            f"Research the topic: '{request.topic}'{context_str}\n"
                            "Gather comprehensive information from available sources. "
                            "Present findings in a structured format with key facts and sources."
                        ),
                        expected_output="A structured research report with key findings, facts, and sources.",
                        agent=agents[i],
                    )
                )
            elif role == AgentRole.ANALYST:
                tasks.append(
                    Task(
                        description=(
                            f"Analyze the research findings about: '{request.topic}'\n"
                            "Identify patterns, trends, and strategic implications. "
                            "Provide data-driven insights and recommendations."
                        ),
                        expected_output="An analytical report with insights, patterns, and recommendations.",
                        agent=agents[i],
                    )
                )
            elif role == AgentRole.WRITER:
                tasks.append(
                    Task(
                        description=(
                            f"Write a comprehensive report about: '{request.topic}'\n"
                            "Based on the research and analysis, create a clear, well-structured "
                            "document. Use headings, bullet points, and clear language."
                        ),
                        expected_output="A polished, well-structured report ready for publication.",
                        agent=agents[i],
                    )
                )
            elif role == AgentRole.CRITIC:
                tasks.append(
                    Task(
                        description=(
                            f"Review the report about: '{request.topic}'\n"
                            "Check for accuracy, completeness, logical consistency, and clarity. "
                            "Provide specific feedback or approve the final version."
                        ),
                        expected_output="A quality review with specific feedback or final approval.",
                        agent=agents[i],
                    )
                )

        return tasks
