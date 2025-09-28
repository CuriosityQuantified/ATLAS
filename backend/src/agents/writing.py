"""
Writing Agent for ATLAS
Handles document creation, file operations, and content generation
"""

import logging
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from src.agents.base import BaseAgent, Task, TaskResult, AgentStatus
from src.agents.agent_factory import LettaAgentFactory
from src.tools import file_tool, planning_tool, todo_tool

logger = logging.getLogger(__name__)


class WritingAgent(BaseAgent):
    """
    WritingAgent specializes in document creation, file operations, and content generation.

    This agent manages the writing process including:
    - Creating structured documents
    - Managing file operations
    - Adding proper citations and references
    - Exporting content in multiple formats
    - Planning and tracking writing tasks
    """

    def __init__(
        self,
        agent_id: str,
        letta_agent,
        factory: LettaAgentFactory,
        task_id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the WritingAgent with Letta integration and tool registration.

        Args:
            agent_id: Unique identifier for this agent instance
            letta_agent: Letta agent instance for memory and conversation
            factory: LettaAgentFactory instance for agent management
            task_id: Optional task ID for this agent's work
            **kwargs: Additional arguments passed to BaseAgent
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="Writing Agent",
            task_id=task_id,
            **kwargs
        )

        self.letta_agent = letta_agent
        self.factory = factory

        # Register tools with the agent
        self._register_tools()

        logger.info(f"WritingAgent {agent_id} initialized with Letta integration")

    def _register_tools(self) -> None:
        """Register all tools with their descriptions for the Letta agent."""

        tools = [
            # Document creation tools
            {
                "function": self.create_document,
                "name": "create_document",
                "description": "Create a structured document with proper formatting. Use for generating reports, briefs, and structured content."
            },
            {
                "function": self.add_citations,
                "name": "add_citations",
                "description": "Add proper citations and references to a document. Use to ensure proper attribution and source tracking."
            },
            {
                "function": self.export_format,
                "name": "export_format",
                "description": "Export document content in specified format (PDF, Markdown, HTML). Use for final output generation."
            },

            # File operation tools
            {
                "function": self.list_files,
                "name": "list_files",
                "description": "Explore the file repository to see available content. Use to understand what files exist before reading or creating."
            },
            {
                "function": self.read_file,
                "name": "read_file",
                "description": "Read content from an existing file. Use to access previous work or reference materials."
            },
            {
                "function": self.create_file,
                "name": "create_file",
                "description": "Create a new file with specified content. Use when generating new outputs or saving drafts."
            },
            {
                "function": self.update_file,
                "name": "update_file",
                "description": "Update existing file content. Use for revisions, additions, or corrections to existing files."
            },

            # Planning and progress tools (namespaced)
            {
                "function": self.plan_writing,
                "name": "plan_writing",
                "description": "Create a structured plan for writing tasks. Use to break down complex writing projects into manageable steps."
            },
            {
                "function": self.track_writing_progress,
                "name": "track_writing_progress",
                "description": "Track progress on writing tasks and todos. Use to manage and update task completion status."
            }
        ]

        # Note: In a full implementation, these tools would be registered with the Letta agent
        # For now, we store them for reference
        self.available_tools = tools
        logger.info(f"Registered {len(tools)} tools for WritingAgent {self.agent_id}")

    async def process_delegation(self, task: Task, context: Dict[str, Any]) -> TaskResult:
        """
        Process a writing task delegation with context provided as XML message.

        Args:
            task: The writing task to process
            context: Additional context including requirements, sources, format preferences

        Returns:
            TaskResult with the completed writing work
        """
        start_time = datetime.now()

        try:
            await self.update_status(AgentStatus.PROCESSING, f"Processing writing task: {task.task_type}")

            # Format context as XML message (not system prompt)
            xml_context = self._format_context_as_xml(task, context)

            # Send XML context as a message to the Letta agent
            messages = self.factory.send_message_to_agent(
                agent_id=self.letta_agent.id,
                message=xml_context
            )

            # Process the agent's response
            if messages:
                # Extract the main response content
                response_content = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])

                # Create successful result
                processing_time = (datetime.now() - start_time).total_seconds()

                result = TaskResult(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    result_type="writing_output",
                    content=response_content,
                    success=True,
                    processing_time=processing_time,
                    metadata={
                        "writing_type": task.task_type,
                        "context_provided": bool(context),
                        "tools_available": len(self.available_tools),
                        "timestamp": datetime.now().isoformat()
                    }
                )

                await self.update_status(AgentStatus.COMPLETED, "Writing task completed successfully")
                return result

            else:
                # Handle case where no response received
                await self.update_status(AgentStatus.ERROR, "No response from Letta agent")
                return TaskResult(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    result_type="error",
                    content="No response received from writing agent",
                    success=False,
                    processing_time=(datetime.now() - start_time).total_seconds(),
                    errors=["Agent did not respond to delegation"]
                )

        except Exception as e:
            await self.update_status(AgentStatus.ERROR, f"Error processing writing task: {str(e)}")
            logger.error(f"WritingAgent {self.agent_id} error: {e}", exc_info=True)

            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                result_type="error",
                content=f"Writing task failed: {str(e)}",
                success=False,
                processing_time=(datetime.now() - start_time).total_seconds(),
                errors=[str(e)]
            )

    def _format_context_as_xml(self, task: Task, context: Dict[str, Any]) -> str:
        """
        Format task and context information as XML message.

        Args:
            task: The writing task to format
            context: Additional context to include

        Returns:
            XML-formatted string with all context information
        """
        xml_parts = [
            "<writing_task>",
            f"  <task_id>{task.task_id}</task_id>",
            f"  <task_type>{task.task_type}</task_type>",
            f"  <description>{task.description}</description>",
            f"  <priority>{task.priority}</priority>"
        ]

        if task.deadline:
            xml_parts.append(f"  <deadline>{task.deadline.isoformat()}</deadline>")

        if task.context:
            xml_parts.append("  <task_context>")
            for key, value in task.context.items():
                xml_parts.append(f"    <{key}>{value}</{key}>")
            xml_parts.append("  </task_context>")

        if context:
            xml_parts.append("  <delegation_context>")
            for key, value in context.items():
                if isinstance(value, (dict, list)):
                    xml_parts.append(f"    <{key}>{json.dumps(value)}</{key}>")
                else:
                    xml_parts.append(f"    <{key}>{value}</{key}>")
            xml_parts.append("  </delegation_context>")

        xml_parts.extend([
            "  <available_tools>",
            "    <tools>create_document, add_citations, export_format, list_files, read_file, create_file, update_file, plan_writing, track_writing_progress</tools>",
            "    <description>Use these tools to complete the writing task effectively</description>",
            "  </available_tools>",
            "</writing_task>"
        ])

        return "\n".join(xml_parts)

    async def process_task(self, task: Task) -> TaskResult:
        """
        Process a writing task (required by BaseAgent).

        Args:
            task: The task to process

        Returns:
            TaskResult with the completed work
        """
        # Delegate to process_delegation with empty context
        return await self.process_delegation(task, {})

    # Tool implementations

    def create_document(
        self,
        title: str,
        content: str,
        document_type: str = "report",
        sections: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a structured document with proper formatting.

        Args:
            title: Document title
            content: Main document content
            document_type: Type of document (report, brief, memo, etc.)
            sections: Optional list of section headers
            metadata: Optional document metadata

        Returns:
            Information about the created document
        """
        try:
            # Create structured document content
            doc_content = f"# {title}\n\n"

            if metadata:
                doc_content += "## Document Information\n"
                for key, value in metadata.items():
                    doc_content += f"- **{key.title()}**: {value}\n"
                doc_content += "\n"

            if sections:
                # Structure content by sections
                doc_content += content
                for section in sections:
                    doc_content += f"\n## {section}\n\n[Content for {section}]\n"
            else:
                doc_content += content

            # Save using file tool
            filename = f"{title.lower().replace(' ', '_')}_{document_type}"
            result = file_tool.save_output(
                filename=filename,
                content=doc_content,
                file_type="markdown",
                subdirectory="reports",
                metadata={
                    "document_type": document_type,
                    "created_by": self.agent_id,
                    "sections": sections or [],
                    **(metadata or {})
                }
            )

            logger.info(f"Created document: {title} ({document_type})")
            return result

        except Exception as e:
            logger.error(f"Error creating document: {e}")
            return {"status": "error", "error": str(e)}

    def add_citations(
        self,
        filename: str,
        citations: List[Dict[str, str]],
        citation_style: str = "APA"
    ) -> Dict[str, Any]:
        """
        Add proper citations and references to a document.

        Args:
            filename: Name of the file to add citations to
            citations: List of citation dictionaries with source information
            citation_style: Citation style to use (APA, MLA, Chicago)

        Returns:
            Status of citation addition
        """
        try:
            # Load existing file
            file_result = file_tool.load_file(filename)
            if file_result["status"] != "success":
                return file_result

            content = file_result["content"]

            # Generate citations section
            citations_section = "\n\n## References\n\n"

            for i, citation in enumerate(citations, 1):
                if citation_style.upper() == "APA":
                    # Simple APA format
                    author = citation.get("author", "Unknown Author")
                    year = citation.get("year", "n.d.")
                    title = citation.get("title", "Untitled")
                    url = citation.get("url", "")

                    cite_text = f"{i}. {author} ({year}). {title}."
                    if url:
                        cite_text += f" Retrieved from {url}"
                    citations_section += cite_text + "\n"
                else:
                    # Basic format for other styles
                    citations_section += f"{i}. {citation}\n"

            # Update file with citations
            updated_content = content + citations_section
            result = file_tool.save_output(
                filename=filename,
                content=updated_content,
                file_type="markdown",
                metadata={"citations_added": len(citations), "citation_style": citation_style}
            )

            logger.info(f"Added {len(citations)} citations to {filename}")
            return result

        except Exception as e:
            logger.error(f"Error adding citations: {e}")
            return {"status": "error", "error": str(e)}

    def export_format(
        self,
        filename: str,
        format_type: str,
        output_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export document content in specified format.

        Args:
            filename: Source file to export
            format_type: Target format (PDF, HTML, markdown)
            output_name: Optional custom output filename

        Returns:
            Information about the exported file
        """
        try:
            # Load source file
            file_result = file_tool.load_file(filename)
            if file_result["status"] != "success":
                return file_result

            content = file_result["content"]

            # Determine output filename
            if not output_name:
                base_name = Path(filename).stem
                output_name = f"{base_name}_export"

            # Simple format conversion (in a full implementation, would use pandoc or similar)
            if format_type.lower() == "html":
                # Basic markdown to HTML conversion
                html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{output_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1, h2, h3 {{ color: #333; }}
        pre {{ background: #f4f4f4; padding: 10px; }}
    </style>
</head>
<body>
    <pre>{content}</pre>
</body>
</html>"""
                result = file_tool.save_output(
                    filename=output_name,
                    content=html_content,
                    file_type="text",  # Will add .txt, we'll override
                    subdirectory="reports"
                )
                # Update the path to have .html extension
                if result["status"] == "success":
                    old_path = Path(result["file_path"])
                    new_path = old_path.with_suffix(".html")
                    old_path.rename(new_path)
                    result["file_path"] = str(new_path)
                    result["format"] = "HTML"

            else:
                # For PDF and other formats, save as markdown for now
                result = file_tool.save_output(
                    filename=output_name,
                    content=content,
                    file_type="markdown",
                    subdirectory="reports",
                    metadata={"exported_from": filename, "target_format": format_type}
                )
                result["format"] = format_type
                result["note"] = f"Exported as markdown. Convert to {format_type} manually if needed."

            logger.info(f"Exported {filename} to {format_type} format")
            return result

        except Exception as e:
            logger.error(f"Error exporting format: {e}")
            return {"status": "error", "error": str(e)}

    def list_files(
        self,
        subdirectory: Optional[str] = None,
        file_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Explore the file repository to see available content.

        Args:
            subdirectory: Optional filter by subdirectory
            file_type: Optional filter by file type

        Returns:
            List of available files with their information
        """
        try:
            return file_tool.list_outputs(subdirectory=subdirectory, file_type=file_type)
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return [{"error": str(e)}]

    def read_file(self, filename: str, subdirectory: Optional[str] = None) -> Dict[str, Any]:
        """
        Read content from an existing file.

        Args:
            filename: Name of the file to read
            subdirectory: Optional subdirectory to search in

        Returns:
            File content and metadata
        """
        try:
            return file_tool.load_file(filename=filename, subdirectory=subdirectory)
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return {"status": "error", "error": str(e)}

    def create_file(
        self,
        filename: str,
        content: str,
        file_type: str = "text",
        subdirectory: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new file with specified content.

        Args:
            filename: Name of the file to create
            content: Content to write
            file_type: Type of file (text, json, markdown, yaml)
            subdirectory: Optional subdirectory within session
            metadata: Optional metadata about the file

        Returns:
            Information about the created file
        """
        try:
            enhanced_metadata = {
                "created_by": self.agent_id,
                "creation_time": datetime.now().isoformat(),
                **(metadata or {})
            }
            return file_tool.save_output(
                filename=filename,
                content=content,
                file_type=file_type,
                subdirectory=subdirectory,
                metadata=enhanced_metadata
            )
        except Exception as e:
            logger.error(f"Error creating file: {e}")
            return {"status": "error", "error": str(e)}

    def update_file(
        self,
        filename: str,
        content: str,
        update_type: str = "append",
        subdirectory: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update existing file content.

        Args:
            filename: Name of the file to update
            content: Content to add or replace with
            update_type: Type of update (append, replace)
            subdirectory: Optional subdirectory within session

        Returns:
            Status information about the update
        """
        try:
            if update_type == "append":
                return file_tool.append_content(
                    filename=filename,
                    content=content,
                    subdirectory=subdirectory
                )
            else:  # replace
                return file_tool.save_output(
                    filename=filename,
                    content=content,
                    subdirectory=subdirectory,
                    metadata={"updated_by": self.agent_id, "update_type": "replace"}
                )
        except Exception as e:
            logger.error(f"Error updating file: {e}")
            return {"status": "error", "error": str(e)}

    def plan_writing(
        self,
        task_description: str,
        context: str = "",
        document_type: str = "report"
    ) -> Dict[str, Any]:
        """
        Create a structured plan for writing tasks (namespaced to this agent).

        Args:
            task_description: The writing task to plan
            context: Additional context for planning
            document_type: Type of document to create

        Returns:
            Structured writing plan
        """
        try:
            # Use namespaced planning for this agent
            enhanced_context = f"{context}\n\nDocument Type: {document_type}\nAgent: {self.agent_id}"
            return planning_tool.plan_task(
                task_description=task_description,
                context=enhanced_context,
                agent_memory=None,
                agent_namespace=self.agent_id  # Use agent ID as namespace
            )
        except Exception as e:
            logger.error(f"Error planning writing task: {e}")
            return {"status": "error", "error": str(e)}

    def track_writing_progress(
        self,
        task_id: str,
        status: str,
        result: Optional[Any] = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Track progress on writing tasks and todos (namespaced to this agent).

        Args:
            task_id: The task to update
            status: New status (pending/in_progress/completed/failed)
            result: Optional result data if completed
            error: Optional error message if failed

        Returns:
            Updated todo information
        """
        try:
            return todo_tool.update_todo_status(
                task_id=task_id,
                status=status,
                result=result,
                error=error,
                agent_namespace=self.agent_id  # Use agent ID as namespace
            )
        except Exception as e:
            logger.error(f"Error tracking writing progress: {e}")
            return {"status": "error", "error": str(e)}