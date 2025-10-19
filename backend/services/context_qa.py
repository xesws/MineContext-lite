"""Context-aware Q&A service using RAG (Retrieval-Augmented Generation)."""

from typing import Dict, List, Optional

from loguru import logger

from backend.config import settings
from backend.database import db
from backend.utils.embedding_utils import embedding_service
from backend.vector_store import vector_store


class ContextQAService:
    """Retrieval-Augmented Generation service for context-aware Q&A."""

    def __init__(self):
        """Initialize context Q&A service."""
        pass

    def is_available(self) -> bool:
        """Check if service is available.

        Returns:
            True if all dependencies are available
        """
        return (
            settings.ai.enabled
            and embedding_service.is_available()
            and vector_store.is_available()
        )

    async def ask_question(
        self,
        question: str,
        top_k: int = 5,
        include_context: bool = True
    ) -> Dict:
        """Answer a question using context from screenshots.

        Args:
            question: User's question
            top_k: Number of relevant screenshots to retrieve
            include_context: Whether to include retrieved context in response

        Returns:
            Dictionary with answer and supporting context
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'Q&A service not available. Enable AI and vector search.'
            }

        try:
            # Step 1: Generate embedding for the question
            question_embedding = embedding_service.generate_embedding(question)

            if question_embedding is None:
                return {
                    'success': False,
                    'error': 'Failed to generate question embedding'
                }

            # Step 2: Retrieve relevant contexts
            similar_items = vector_store.search_similar(
                query_embedding=question_embedding,
                top_k=top_k,
                min_similarity=0.3  # Lower threshold for Q&A
            )

            if not similar_items:
                return {
                    'success': True,
                    'answer': "I couldn't find any relevant information in your screenshots to answer this question.",
                    'relevant_screenshots': [],
                    'confidence': 0.0
                }

            # Step 3: Prepare context for AI
            context_texts = []
            relevant_screenshots = []

            for item in similar_items:
                screenshot_id = item['screenshot_id']
                screenshot = db.get_screenshot(screenshot_id)

                if screenshot and screenshot.description:
                    context_texts.append(f"[{screenshot.timestamp}] {screenshot.description}")
                    relevant_screenshots.append({
                        'id': screenshot_id,
                        'timestamp': screenshot.timestamp.isoformat(),
                        'description': screenshot.description,
                        'similarity': item['similarity']
                    })

            # Step 4: Generate answer using AI
            answer_prompt = self._build_qa_prompt(question, context_texts)

            from backend.utils.ai_utils import get_vision_client

            # For now, return the context-based response
            # TODO: Implement text-only LLM call for better answers
            answer = self._generate_context_answer(question, context_texts)

            avg_confidence = sum(s['similarity'] for s in relevant_screenshots) / len(relevant_screenshots)

            return {
                'success': True,
                'answer': answer,
                'relevant_screenshots': relevant_screenshots if include_context else [],
                'confidence': round(avg_confidence, 2),
                'sources_count': len(relevant_screenshots)
            }

        except Exception as e:
            logger.error(f"Error in Q&A: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _build_qa_prompt(self, question: str, contexts: List[str]) -> str:
        """Build prompt for Q&A with retrieved context.

        Args:
            question: User's question
            contexts: Retrieved context texts

        Returns:
            Complete prompt for AI
        """
        context_str = "\n\n".join(contexts)

        return f"""You are a helpful assistant that answers questions based on the user's screenshot history.

Context from screenshots:
{context_str}

Question: {question}

Please provide a concise, accurate answer based on the context above. If the context doesn't contain enough information, say so clearly.

Answer:"""

    def _generate_context_answer(self, question: str, contexts: List[str]) -> str:
        """Generate a basic answer from context (fallback method).

        Args:
            question: User's question
            contexts: Retrieved contexts

        Returns:
            Generated answer
        """
        if not contexts:
            return "I couldn't find relevant information in your screenshots."

        # Simple extraction-based answer
        answer = "Based on your screenshots, here's what I found:\n\n"

        for i, context in enumerate(contexts[:3], 1):
            answer += f"{i}. {context}\n"

        answer += f"\n(Found {len(contexts)} relevant screenshot(s))"

        return answer

    async def find_related_work(
        self,
        topic: str,
        days: Optional[int] = None,
        top_k: int = 10
    ) -> Dict:
        """Find all work related to a specific topic.

        Args:
            topic: Topic or keyword to search for
            days: Limit to last N days (optional)
            top_k: Maximum results to return

        Returns:
            Related work findings
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'Service not available'
            }

        try:
            # Generate embedding for topic
            topic_embedding = embedding_service.generate_embedding(topic)

            if topic_embedding is None:
                return {
                    'success': False,
                    'error': 'Failed to generate topic embedding'
                }

            # Search for similar content
            similar_items = vector_store.search_similar(
                query_embedding=topic_embedding,
                top_k=top_k * 2,  # Get more for filtering
                min_similarity=0.4
            )

            # Filter by date if specified
            if days:
                from datetime import datetime, timedelta
                cutoff = datetime.now() - timedelta(days=days)

                similar_items = [
                    item for item in similar_items
                    if item.get('timestamp') and datetime.fromisoformat(item['timestamp']) >= cutoff
                ]

            # Organize results
            results = []
            for item in similar_items[:top_k]:
                screenshot = db.get_screenshot(item['screenshot_id'])
                if screenshot:
                    results.append({
                        'screenshot_id': screenshot.id,
                        'timestamp': screenshot.timestamp.isoformat(),
                        'description': screenshot.description,
                        'app_name': screenshot.app_name,
                        'similarity': item['similarity']
                    })

            return {
                'success': True,
                'topic': topic,
                'results': results,
                'count': len(results)
            }

        except Exception as e:
            logger.error(f"Error finding related work: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def summarize_topic(self, topic: str, days: int = 7) -> Dict:
        """Generate a summary of all work on a topic.

        Args:
            topic: Topic to summarize
            days: Number of days to look back

        Returns:
            Topic summary
        """
        try:
            # Find related work
            related = await self.find_related_work(topic, days=days, top_k=20)

            if not related['success'] or not related['results']:
                return {
                    'success': True,
                    'summary': f"No work found on '{topic}' in the last {days} days."
                }

            # Group by date
            from collections import defaultdict
            by_date = defaultdict(list)

            for result in related['results']:
                date = result['timestamp'].split('T')[0]
                by_date[date].append(result)

            # Generate summary
            summary = f"# Work Summary: {topic}\n\n"
            summary += f"Period: Last {days} days\n"
            summary += f"Total screenshots found: {len(related['results'])}\n\n"

            summary += "## Timeline:\n\n"
            for date in sorted(by_date.keys(), reverse=True):
                items = by_date[date]
                summary += f"### {date} ({len(items)} screenshots)\n"
                for item in items[:3]:  # Top 3 per day
                    summary += f"- {item['description'][:100]}...\n"
                summary += "\n"

            return {
                'success': True,
                'summary': summary,
                'screenshot_count': len(related['results']),
                'days_covered': len(by_date)
            }

        except Exception as e:
            logger.error(f"Error summarizing topic: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Global context Q&A service instance
context_qa_service = ContextQAService()
