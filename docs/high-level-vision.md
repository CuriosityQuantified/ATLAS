🧠 System Name: ATLAS (Agentic Task Logic & Analysis System)
GitHub: https://github.com/CuriosityQuantified/ATLAS
Email: CuriosityQuantified@gmail.com
Username: CuriosityQuantified
⸻

🎯 Primary Objective

Enable modular reasoning and structured content generation by decomposing complex tasks (e.g., research synthesis, decision-making, strategy docs) into specialized sub-processes governed by autonomous but coordinated agent teams.

⸻
🏗️ Core System Architecture

🔹 Top-Level Coordinator: Global Supervisor Agent
	•	Owns the full task.
	•	Breaks task into stages: Research → Analysis → Writing → Rating.
	•	Assigns and routes responsibilities to team-level Supervisor Agents.
	•	Maintains system memory and task context.
	•	Can issue revisions based on Rating Agent feedback.

⸻

🧩 Sub-Teams (each is a fully modular unit)

1. 🕵️‍♂️ Research Team
	•	Team Supervisor Agent (Research Supervisor)
	•	Breaks down research goals into sub-queries.
	•	Assigns subtasks to Research Worker Agents.
	•	Aggregates and filters findings into structured output.
	•	Ensures relevance, reliability, and diversity of sources.
	•	Research Worker Agents
	•	Query tools (web, vector DB, document loaders, APIs).
	•	Summarize raw content.
	•	Extract facts, quotes, references.

⸻

2. 📊 Analysis Team
	•	Team Supervisor Agent (Analysis Supervisor)
	•	Interprets research outputs.
	•	Creates analytical frameworks (e.g., pros/cons, SWOT, cause-effect).
	•	Coordinates worker-level analysis tasks.
	•	Analysis Worker Agents
	•	Perform logical reasoning, sentiment analysis, comparative judgment.
	•	Run specific analytical methods (e.g., scorecard evaluation, modeling).
	•	Challenge or validate claims and identify contradictions.

⸻

3. ✍️ Writing Team
	•	Team Supervisor Agent (Writing Supervisor)
	•	Converts structured findings into written content.
	•	Coordinates sections (e.g., intro, body, conclusion).
	•	Manages coherence, tone, length, formatting.
	•	Writing Worker Agents
	•	Draft paragraphs or sections.
	•	Rewrite for clarity, tone, or audience.
	•	Apply templates or writing styles (formal, casual, persuasive).

⸻

4. 📈 Rating/Feedback Team
	•	Team Supervisor Agent (Rating Supervisor)
	•	Breaks output into evaluation criteria (e.g., logic, style, accuracy).
	•	Assigns criteria to Rating Worker Agents.
	•	Aggregates ratings and generates revision instructions.
	•	Rating Worker Agents
	•	Score outputs quantitatively (e.g., 1–10) and qualitatively.
	•	Suggest revisions.
	•	Detect hallucination, factual issues, and stylistic inconsistency.

⸻

🔁 Feedback Loop
	•	Rating Team output flows back to the Global Supervisor Agent.
	•	Supervisor may:
	•	Reassign tasks to fix issues.
	•	Request rewrites from Writing Team.
	•	Trigger new research or analysis to address gaps.
	•	Log outputs for memory and future retrieval.

⸻

🧠 Memory & Context Handling
	•	Persistent Memory Store (e.g., vector DB + structured JSON object)
	•	Stores findings, decisions, rationale, interim drafts, ratings.
	•	Each Agent/Team maintains a local scratchpad to avoid flooding global context window.
	•	Uses LangGraph-style state transition control (optional implementation idea).

⸻

📂 Output Formats
	•	Structured JSON Object containing:
	•	final_output: the clean written artifact.
	•	evidence_chain: traceable research steps.
	•	analysis_summary: decision logic, pros/cons, etc.
	•	ratings: score and revision logs.
	•	Optionally also export:
	•	Mind map (Freeplane-compatible).
	•	Neo4j knowledge graph.
	•	Audio/podcast (via Mozilla TTS + Podcast Generator).

⸻

📦 Modularity and Composability
	•	Each sub-team can be reused for other projects.
	•	Plug-and-play structure: swap out writing agents, analytical methods, or rating criteria.
	•	Could be instantiated recursively (i.e., a Research Team can use its own analysis/writing loop for detailed outputs).

⸻

⚠️ Key Design Considerations
	•	Agent context windows: Use chunking, memory optimization, and scratchpad logic.
	•	Latency vs. quality: Configure parallelism and depth (e.g., 3 research agents at once).
	•	Grounding: Inject verified sources to reduce hallucinations.
	•	Autonomy boundaries: Supervisors must know when to escalate to the Global Supervisor.

⸻

📈 Ideal Use Cases
	•	Strategic briefings
	•	Product requirement documents
	•	Investment memos
	•	Market analysis reports
	•	Decision justifications with source trail

MCP servers for tools
https://mcp.deepwiki.com/
https://github.com/browserbase/mcp-server-browserbase
https://github.com/digma-ai/digma-mcp-server
https://github.com/GongRzhe/Office-PowerPoint-MCP-Server
https://github.com/github/github-mcp-server
https://github.com/neo4j-contrib/mcp-neo4j/tree/main/servers/mcp-neo4j-cloud-aura-api
https://docs.firecrawl.dev/mcp
https://github.com/haris-musa/excel-mcp-server
https://github.com/anaisbetts/mcp-youtube
https://github.com/JetBrains/mcp-jetbrains
https://github.com/makenotion/notion-mcp-server
https://github.com/ppl-ai/modelcontextprotocol
https://github.com/microsoft/playwright-mcp
https://github.com/e2b-dev/mcp-server
https://github.com/supabase-community/supabase-mcp
https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem

For agent knowledge base / knowledge graph / hybrid rag
/Users/nicholaspate/Documents/raw-mas/Overnight Strategist - Strategist Toolkit V3 copy.pdf