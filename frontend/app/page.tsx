"use client";

import { useState, useEffect, useRef } from "react";

interface AgentEvent {
  type: string;
  task_id: string;
  agent: string | null;
  content: string;
  metadata: Record<string, unknown>;
  timestamp: string;
}

interface Task {
  task_id: string;
  topic: string;
  status: string;
  crew_mode: string;
  agents: string[];
  created_at: string;
  completed_at: string | null;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8400";
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8400";

export default function Home() {
  const [topic, setTopic] = useState("");
  const [crewMode, setCrewMode] = useState<"sequential" | "hierarchical">(
    "sequential"
  );
  const [tasks, setTasks] = useState<Task[]>([]);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const eventsEndRef = useRef<HTMLDivElement>(null);

  // Fetch tasks on load
  useEffect(() => {
    fetchTasks();
  }, []);

  // Connect WebSocket
  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws`);

    ws.onopen = () => console.log("WebSocket connected");
    ws.onmessage = (event) => {
      const data: AgentEvent = JSON.parse(event.data);
      setEvents((prev) => [...prev, data]);
    };
    ws.onclose = () => console.log("WebSocket disconnected");
    ws.onerror = (err) => console.error("WebSocket error:", err);

    wsRef.current = ws;
    return () => ws.close();
  }, []);

  // Auto-scroll events
  useEffect(() => {
    eventsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  async function fetchTasks() {
    const res = await fetch(`${API_URL}/v1/tasks`);
    const data = await res.json();
    setTasks(data);
  }

  async function submitTask() {
    if (!topic.trim()) return;
    setIsSubmitting(true);
    setEvents([]);

    const res = await fetch(`${API_URL}/v1/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        topic,
        crew_mode: crewMode,
        agents: ["researcher", "analyst", "writer", "critic"],
      }),
    });

    const data = await res.json();
    setActiveTaskId(data.task_id);
    setIsSubmitting(false);
    setTopic("");
    fetchTasks();
  }

  function getAgentColor(agent: string | null): string {
    const colors: Record<string, string> = {
      researcher: "text-blue-400",
      analyst: "text-green-400",
      writer: "text-purple-400",
      critic: "text-orange-400",
    };
    return agent ? colors[agent] || "text-gray-400" : "text-gray-400";
  }

  function getEventIcon(type: string): string {
    const icons: Record<string, string> = {
      task_started: "🚀",
      agent_thinking: "🤔",
      agent_action: "⚡",
      agent_result: "✅",
      agent_delegation: "🔄",
      crew_progress: "📊",
      task_completed: "🎉",
      task_failed: "❌",
      error: "⚠️",
    };
    return icons[type] || "📌";
  }

  return (
    <main className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">
          🤖 AI Multi-Agent Platform
        </h1>

        {/* Task Submission */}
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Submit Task</h2>
          <div className="flex gap-4">
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Enter a topic for the crew..."
              className="flex-1 bg-gray-700 rounded px-4 py-2 text-white placeholder-gray-400"
              onKeyDown={(e) => e.key === "Enter" && submitTask()}
            />
            <select
              value={crewMode}
              onChange={(e) =>
                setCrewMode(
                  e.target.value as "sequential" | "hierarchical"
                )
              }
              className="bg-gray-700 rounded px-4 py-2"
            >
              <option value="sequential">Sequential</option>
              <option value="hierarchical">Hierarchical</option>
            </select>
            <button
              onClick={submitTask}
              disabled={isSubmitting || !topic.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-6 py-2 rounded font-semibold"
            >
              {isSubmitting ? "Submitting..." : "Run Crew"}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Agent Activity Stream */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">
              📡 Agent Activity Stream
            </h2>
            <div className="h-96 overflow-y-auto space-y-2">
              {events.length === 0 ? (
                <p className="text-gray-500">
                  Submit a task to see agent activity...
                </p>
              ) : (
                events.map((event, i) => (
                  <div
                    key={i}
                    className="bg-gray-700 rounded p-3 text-sm"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span>{getEventIcon(event.type)}</span>
                      {event.agent && (
                        <span
                          className={`font-semibold ${getAgentColor(event.agent)}`}
                        >
                          {event.agent}
                        </span>
                      )}
                      <span className="text-gray-400 text-xs">
                        {event.type}
                      </span>
                    </div>
                    <p className="text-gray-300">
                      {event.content.slice(0, 300)}
                      {event.content.length > 300 && "..."}
                    </p>
                  </div>
                ))
              )}
              <div ref={eventsEndRef} />
            </div>
          </div>

          {/* Task History */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">📋 Task History</h2>
            <div className="h-96 overflow-y-auto space-y-2">
              {tasks.length === 0 ? (
                <p className="text-gray-500">No tasks yet.</p>
              ) : (
                tasks.map((task) => (
                  <div
                    key={task.task_id}
                    className="bg-gray-700 rounded p-3 cursor-pointer hover:bg-gray-600"
                    onClick={() => setActiveTaskId(task.task_id)}
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-semibold">
                        {task.topic.slice(0, 50)}
                      </span>
                      <span
                        className={`text-xs px-2 py-1 rounded ${
                          task.status === "completed"
                            ? "bg-green-900 text-green-300"
                            : task.status === "running"
                              ? "bg-blue-900 text-blue-300"
                              : task.status === "failed"
                                ? "bg-red-900 text-red-300"
                                : "bg-gray-600 text-gray-300"
                        }`}
                      >
                        {task.status}
                      </span>
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      {task.crew_mode} · {task.agents.length} agents
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
