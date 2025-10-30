"""Import/Export service for TodoList module."""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger

from todolist.backend import database as todo_db
from todolist.backend.services.todo_manager import TodoManager


class ImportExportService:
    """Service for importing and exporting TODOs."""

    def __init__(self, db_connection):
        """Initialize import/export service.

        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
        self.todo_manager = TodoManager(db_connection)

    # ===== Markdown Import/Export =====

    def export_to_markdown(self, status_filter: Optional[str] = None) -> str:
        """Export TODOs to Markdown format.

        Args:
            status_filter: Filter by status (pending/in_progress/completed/archived)

        Returns:
            Markdown formatted string

        Format:
            # My TODOs

            ## 学习机器学习 #ML #学习
            - Status: pending
            - Priority: high
            - Estimated: 80 hours
            - Due: 2025-11-01
            - Progress: 60%

            描述内容...

            ### Subtasks
            - [ ] 子任务1
            - [x] 子任务2
        """
        try:
            # Get TODOs
            todos = todo_db.get_user_todos(
                self.conn,
                status=status_filter,
                limit=10000
            )

            # Build markdown
            md_lines = ["# My TODOs\n"]
            md_lines.append(f"*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

            # Get tree structure for root TODOs
            root_todos = [t for t in todos if t['parent_id'] is None]

            for todo in root_todos:
                md_lines.append(self._todo_to_markdown(todo, level=2))

                # Add children
                children = [t for t in todos if t['parent_id'] == todo['id']]
                if children:
                    md_lines.append("\n### Subtasks\n")
                    for child in children:
                        checkbox = "x" if child['status'] == 'completed' else " "
                        md_lines.append(f"- [{checkbox}] {child['title']}\n")

                md_lines.append("\n---\n")

            return "\n".join(md_lines)

        except Exception as e:
            logger.error(f"Error exporting to Markdown: {e}")
            raise

    def _todo_to_markdown(self, todo: Dict, level: int = 2) -> str:
        """Convert single TODO to Markdown format.

        Args:
            todo: TODO dictionary
            level: Header level (2 = ##, 3 = ###)

        Returns:
            Markdown string
        """
        header = "#" * level
        title = todo['title']
        tags = f" {todo['tags']}" if todo['tags'] else ""

        lines = [f"{header} {title}{tags}\n"]

        # Metadata
        lines.append(f"- **Status:** {todo['status']}")
        lines.append(f"- **Priority:** {todo['priority']}")

        if todo.get('estimated_hours'):
            lines.append(f"- **Estimated:** {todo['estimated_hours']} hours")

        if todo.get('due_date'):
            lines.append(f"- **Due:** {todo['due_date']}")

        if todo.get('completion_percentage'):
            lines.append(f"- **Progress:** {todo['completion_percentage']}%")

        lines.append("")

        # Description
        if todo.get('description'):
            lines.append(todo['description'])
            lines.append("")

        return "\n".join(lines)

    def import_from_markdown(self, markdown_text: str) -> Dict:
        """Import TODOs from Markdown format.

        Args:
            markdown_text: Markdown formatted string

        Returns:
            Dictionary with import results:
            {
                'success': bool,
                'imported_count': int,
                'errors': List[str]
            }

        Expected format:
            ## TODO Title #tag1 #tag2
            - Status: pending
            - Priority: high
            - Estimated: 10 hours

            Description text...

            ### Subtasks
            - [ ] Subtask 1
            - [x] Subtask 2
        """
        try:
            imported_count = 0
            errors = []

            # Parse markdown sections
            sections = self._parse_markdown_sections(markdown_text)

            for section in sections:
                try:
                    # Create TODO
                    todo_data = self._parse_markdown_section(section)

                    # Create main TODO
                    todo_id = self.todo_manager.create_todo(
                        title=todo_data['title'],
                        description=todo_data.get('description'),
                        priority=todo_data.get('priority', 'medium'),
                        tags=todo_data.get('tags'),
                        due_date=todo_data.get('due_date'),
                        estimated_hours=todo_data.get('estimated_hours')
                    )

                    # Update status if not pending
                    if todo_data.get('status') and todo_data['status'] != 'pending':
                        self.todo_manager.update_todo(
                            todo_id['id'],
                            status=todo_data['status']
                        )

                    imported_count += 1

                    # Create subtasks if any
                    for subtask in todo_data.get('subtasks', []):
                        subtask_id = self.todo_manager.create_todo(
                            title=subtask['title'],
                            parent_id=todo_id['id']
                        )
                        # Update subtask status if completed
                        if subtask['completed']:
                            self.todo_manager.update_todo(
                                subtask_id['id'],
                                status='completed'
                            )
                        imported_count += 1

                except Exception as e:
                    error_msg = f"Failed to import TODO: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            return {
                'success': len(errors) == 0,
                'imported_count': imported_count,
                'errors': errors
            }

        except Exception as e:
            logger.error(f"Error importing from Markdown: {e}")
            return {
                'success': False,
                'imported_count': 0,
                'errors': [str(e)]
            }

    def _parse_markdown_sections(self, markdown_text: str) -> List[str]:
        """Split markdown into TODO sections.

        Args:
            markdown_text: Markdown text

        Returns:
            List of section strings
        """
        # Split by ## headers (TODO sections)
        sections = re.split(r'\n##\s+', markdown_text)
        # Remove title section and empty sections
        return [s.strip() for s in sections[1:] if s.strip() and not s.startswith('#')]

    def _parse_markdown_section(self, section: str) -> Dict:
        """Parse a single TODO section from Markdown.

        Args:
            section: Markdown section text

        Returns:
            Dictionary with TODO data
        """
        lines = section.split('\n')

        # First line is title + tags
        title_line = lines[0].strip()
        title_match = re.match(r'^(.+?)(\s+#.+)?$', title_line)
        title = title_match.group(1).strip() if title_match else title_line
        tags_text = title_match.group(2).strip() if title_match and title_match.group(2) else None

        # Extract tags
        tags = None
        if tags_text:
            tag_matches = re.findall(r'#(\w+)', tags_text)
            tags = ','.join(tag_matches) if tag_matches else None

        # Parse metadata and description
        todo_data = {
            'title': title,
            'tags': tags,
            'description': '',
            'subtasks': []
        }

        in_metadata = True
        in_subtasks = False
        description_lines = []

        for line in lines[1:]:
            line = line.strip()

            if line.startswith('### Subtasks'):
                in_subtasks = True
                in_metadata = False
                continue

            if in_subtasks:
                # Parse subtask checkbox
                subtask_match = re.match(r'-\s+\[([ x])\]\s+(.+)', line)
                if subtask_match:
                    todo_data['subtasks'].append({
                        'title': subtask_match.group(2).strip(),
                        'completed': subtask_match.group(1) == 'x'
                    })
                continue

            if in_metadata and line.startswith('- **'):
                # Parse metadata
                meta_match = re.match(r'-\s+\*\*(.+?):\*\*\s+(.+)', line)
                if meta_match:
                    key = meta_match.group(1).lower()
                    value = meta_match.group(2).strip()

                    if key == 'status':
                        todo_data['status'] = value
                    elif key == 'priority':
                        todo_data['priority'] = value
                    elif key == 'estimated':
                        hours_match = re.search(r'(\d+(?:\.\d+)?)', value)
                        if hours_match:
                            todo_data['estimated_hours'] = float(hours_match.group(1))
                    elif key == 'due':
                        todo_data['due_date'] = value
                    elif key == 'progress':
                        progress_match = re.search(r'(\d+)', value)
                        if progress_match:
                            todo_data['completion_percentage'] = int(progress_match.group(1))
            elif line and not line.startswith('---'):
                in_metadata = False
                description_lines.append(line)

        todo_data['description'] = '\n'.join(description_lines).strip()

        return todo_data

    # ===== JSON Import/Export =====

    def export_to_json(self, status_filter: Optional[str] = None) -> str:
        """Export TODOs to JSON format.

        Args:
            status_filter: Filter by status

        Returns:
            JSON formatted string
        """
        try:
            # Get TODOs with details
            todos = todo_db.get_user_todos(
                self.conn,
                status=status_filter,
                limit=10000
            )

            # Build JSON structure
            export_data = {
                'export_date': datetime.now().isoformat(),
                'version': '1.0',
                'total_count': len(todos),
                'todos': []
            }

            for todo in todos:
                # Remove embedding BLOB for export
                todo_export = {k: v for k, v in todo.items() if k != 'embedding'}

                # Get activities for this TODO
                activities = todo_db.get_todo_activities(self.conn, todo['id'], limit=None)
                todo_export['activities'] = activities

                # Get latest progress
                progress = todo_db.get_latest_progress_snapshot(self.conn, todo['id'])
                if progress:
                    # Parse JSON fields
                    progress['completed_aspects'] = json.loads(progress.get('completed_aspects', '[]'))
                    progress['remaining_aspects'] = json.loads(progress.get('remaining_aspects', '[]'))
                    progress['next_steps'] = json.loads(progress.get('next_steps', '[]'))
                    todo_export['latest_progress'] = progress

                export_data['todos'].append(todo_export)

            return json.dumps(export_data, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            raise

    def import_from_json(self, json_data: Dict) -> Dict:
        """Import TODOs from JSON format.

        Args:
            json_data: Dictionary with TODOs data

        Returns:
            Dictionary with import results
        """
        try:
            imported_count = 0
            errors = []

            todos = json_data.get('todos', [])

            for todo_data in todos:
                try:
                    # Create TODO (skip activities and progress for now)
                    todo_result = self.todo_manager.create_todo(
                        title=todo_data['title'],
                        description=todo_data.get('description'),
                        parent_id=todo_data.get('parent_id'),
                        priority=todo_data.get('priority', 'medium'),
                        tags=todo_data.get('tags'),
                        due_date=todo_data.get('due_date'),
                        estimated_hours=todo_data.get('estimated_hours')
                    )

                    # Update status if specified
                    if todo_data.get('status') and todo_data['status'] != 'pending':
                        self.todo_manager.update_todo(
                            todo_result['id'],
                            status=todo_data['status']
                        )

                    imported_count += 1

                except Exception as e:
                    error_msg = f"Failed to import TODO '{todo_data.get('title', 'Unknown')}': {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            return {
                'success': len(errors) == 0,
                'imported_count': imported_count,
                'errors': errors
            }

        except Exception as e:
            logger.error(f"Error importing from JSON: {e}")
            return {
                'success': False,
                'imported_count': 0,
                'errors': [str(e)]
            }
