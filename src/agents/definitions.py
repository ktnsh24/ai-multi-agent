"""Agent definitions — 4 specialized CrewAI agents."""

from crewai import Agent
from langchain_core.language_models import BaseChatModel

from src.models import AgentRole


def create_researcher(llm: BaseChatModel) -> Agent:
    """Create the Researcher agent — gathers information via RAG and web search."""
    return Agent(
        role="Senior Research Analyst",
        goal="Gather comprehensive, accurate information on the given topic using available tools and knowledge",
        backstory=(
            "You are an expert research analyst with years of experience in data gathering. "
            "You excel at finding relevant information, cross-referencing sources, and "
            "identifying key facts. You always cite your sources and present information "
            "in a structured, easy-to-understand format."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=10,
    )


def create_analyst(llm: BaseChatModel) -> Agent:
    """Create the Analyst agent — analyzes data and draws insights."""
    return Agent(
        role="Data Analyst & Strategist",
        goal="Analyze the research findings to identify patterns, insights, and strategic implications",
        backstory=(
            "You are a senior data analyst who excels at turning raw information into "
            "actionable insights. You use statistical thinking, pattern recognition, and "
            "critical analysis to draw meaningful conclusions. You always support your "
            "analysis with evidence from the research."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=10,
    )


def create_writer(llm: BaseChatModel) -> Agent:
    """Create the Writer agent — generates polished content."""
    return Agent(
        role="Content Writer & Editor",
        goal="Create a clear, well-structured, and engaging report based on the research and analysis",
        backstory=(
            "You are a professional content writer who transforms complex analysis into "
            "clear, engaging prose. You write for a technical audience but keep things "
            "accessible. You use headings, bullet points, and structured sections to "
            "make content scannable."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=10,
    )


def create_critic(llm: BaseChatModel) -> Agent:
    """Create the Critic agent — reviews and provides feedback."""
    return Agent(
        role="Quality Assurance Reviewer",
        goal="Review the written content for accuracy, completeness, and quality. Provide constructive feedback.",
        backstory=(
            "You are a meticulous quality reviewer who checks content for factual accuracy, "
            "logical consistency, completeness, and clarity. You provide specific, actionable "
            "feedback. If the content is good, you approve it. If it needs improvement, you "
            "explain exactly what to fix."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=True,
        max_iter=10,
    )


def create_agent(role: AgentRole, llm: BaseChatModel) -> Agent:
    """Factory function to create an agent by role."""
    factories = {
        AgentRole.RESEARCHER: create_researcher,
        AgentRole.ANALYST: create_analyst,
        AgentRole.WRITER: create_writer,
        AgentRole.CRITIC: create_critic,
    }
    return factories[role](llm)
