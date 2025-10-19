"""AI/LLM integration utilities for MineContext-v2."""

import base64
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from loguru import logger

from backend.config import settings


# Prompt templates
SCREENSHOT_ANALYSIS_PROMPT = """Analyze this screenshot and provide:
1. A concise description of what's shown (1-2 sentences)
2. The main activity or task being performed
3. Relevant tags (comma-separated, max 5 tags)

Focus on:
- Visible application names and UI elements
- The type of work being done (coding, browsing, designing, etc.)
- Key content or topics visible

Format your response as:
DESCRIPTION: [your description]
ACTIVITY: [activity type]
TAGS: [tag1, tag2, tag3]"""


def encode_image_to_base64(image_path: str) -> str:
    """Encode image file to base64 string.

    Args:
        image_path: Path to image file

    Returns:
        Base64 encoded string
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def parse_ai_response(response: str) -> Dict[str, str]:
    """Parse structured AI response into components.

    Args:
        response: Raw AI response text

    Returns:
        Dictionary with description, activity, and tags
    """
    result = {"description": "", "activity": "", "tags": ""}

    lines = response.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("DESCRIPTION:"):
            result["description"] = line.replace("DESCRIPTION:", "").strip()
        elif line.startswith("ACTIVITY:"):
            result["activity"] = line.replace("ACTIVITY:", "").strip()
        elif line.startswith("TAGS:"):
            result["tags"] = line.replace("TAGS:", "").strip()

    # Fallback: use entire response as description if parsing fails
    if not result["description"] and response:
        result["description"] = response.strip()

    return result


class OpenAIVisionClient:
    """OpenAI GPT-4 Vision API client."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI client.

        Args:
            api_key: OpenAI API key (defaults to settings)
        """
        self.api_key = api_key or settings.openai_api_key
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")

    def analyze_screenshot(
        self, image_path: str, prompt: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, str]], Optional[str]]:
        """Analyze screenshot using GPT-4 Vision.

        Args:
            image_path: Path to screenshot file
            prompt: Custom prompt (defaults to SCREENSHOT_ANALYSIS_PROMPT)

        Returns:
            Tuple of (success, result_dict, error_message)
        """
        try:
            prompt = prompt or SCREENSHOT_ANALYSIS_PROMPT
            base64_image = encode_image_to_base64(image_path)

            response = self.client.chat.completions.create(
                model=settings.ai.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=300,
            )

            content = response.choices[0].message.content
            result = parse_ai_response(content)

            logger.info(f"OpenAI analysis successful for {image_path}")
            return True, result, None

        except Exception as e:
            error_msg = f"OpenAI analysis failed: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg


class AnthropicVisionClient:
    """Anthropic Claude Vision API client."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Anthropic client.

        Args:
            api_key: Anthropic API key (defaults to settings)
        """
        self.api_key = api_key or settings.anthropic_api_key
        if not self.api_key:
            raise ValueError("Anthropic API key not configured")

        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Install with: pip install anthropic")

    def analyze_screenshot(
        self, image_path: str, prompt: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, str]], Optional[str]]:
        """Analyze screenshot using Claude Vision.

        Args:
            image_path: Path to screenshot file
            prompt: Custom prompt (defaults to SCREENSHOT_ANALYSIS_PROMPT)

        Returns:
            Tuple of (success, result_dict, error_message)
        """
        try:
            prompt = prompt or SCREENSHOT_ANALYSIS_PROMPT
            base64_image = encode_image_to_base64(image_path)

            # Detect image format
            image_format = Path(image_path).suffix.lower().replace(".", "")
            if image_format == "jpg":
                image_format = "jpeg"

            message = self.client.messages.create(
                model=settings.ai.model,
                max_tokens=300,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": f"image/{image_format}",
                                    "data": base64_image,
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            )

            content = message.content[0].text
            result = parse_ai_response(content)

            logger.info(f"Anthropic analysis successful for {image_path}")
            return True, result, None

        except Exception as e:
            error_msg = f"Anthropic analysis failed: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg


class OpenRouterVisionClient:
    """OpenRouter API client (supports multiple vision models)."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key (defaults to settings)
        """
        self.api_key = api_key or settings.openrouter_api_key
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")

        try:
            from openai import OpenAI
            # OpenRouter uses OpenAI-compatible API
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")

    def analyze_screenshot(
        self, image_path: str, prompt: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, str]], Optional[str]]:
        """Analyze screenshot using OpenRouter.

        Args:
            image_path: Path to screenshot file
            prompt: Custom prompt (defaults to SCREENSHOT_ANALYSIS_PROMPT)

        Returns:
            Tuple of (success, result_dict, error_message)
        """
        try:
            prompt = prompt or SCREENSHOT_ANALYSIS_PROMPT
            base64_image = encode_image_to_base64(image_path)

            response = self.client.chat.completions.create(
                model=settings.ai.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=300,
            )

            content = response.choices[0].message.content
            result = parse_ai_response(content)

            logger.info(f"OpenRouter analysis successful for {image_path}")
            return True, result, None

        except Exception as e:
            error_msg = f"OpenRouter analysis failed: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg


def get_vision_client():
    """Get the appropriate vision client based on configuration.

    Returns:
        Vision client instance

    Raises:
        ValueError: If AI is not enabled or provider is invalid
    """
    if not settings.ai.enabled:
        raise ValueError("AI features are not enabled")

    provider = settings.ai.provider.lower()

    if provider == "openai":
        return OpenAIVisionClient()
    elif provider == "anthropic":
        return AnthropicVisionClient()
    elif provider == "openrouter":
        return OpenRouterVisionClient()
    else:
        raise ValueError(f"Unknown AI provider: {provider}")


async def analyze_screenshot_async(
    image_path: str, prompt: Optional[str] = None
) -> Tuple[bool, Optional[Dict[str, str]], Optional[str]]:
    """Analyze screenshot asynchronously (wrapper for sync function).

    Args:
        image_path: Path to screenshot file
        prompt: Custom prompt (defaults to SCREENSHOT_ANALYSIS_PROMPT)

    Returns:
        Tuple of (success, result_dict, error_message)
    """
    try:
        client = get_vision_client()
        return client.analyze_screenshot(image_path, prompt)
    except Exception as e:
        error_msg = f"Failed to get vision client: {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg


def extract_tags_from_description(description: str, max_tags: int = 5) -> List[str]:
    """Extract potential tags from a description using simple heuristics.

    Args:
        description: Description text
        max_tags: Maximum number of tags to return

    Returns:
        List of tags
    """
    # Common activity keywords
    activity_keywords = {
        "code", "coding", "programming", "development", "debug", "debugging",
        "browse", "browsing", "web", "internet", "search", "reading",
        "design", "designing", "edit", "editing", "create", "creating",
        "write", "writing", "document", "email", "chat", "messaging",
        "video", "watch", "watching", "meeting", "conference",
        "terminal", "command", "shell", "database", "data"
    }

    # Common application keywords
    app_keywords = {
        "vscode", "chrome", "firefox", "safari", "slack", "zoom",
        "terminal", "finder", "explorer", "photoshop", "figma",
        "notion", "github", "gitlab", "jira", "trello"
    }

    description_lower = description.lower()
    found_tags = []

    # Find activity keywords
    for keyword in activity_keywords:
        if keyword in description_lower and keyword not in found_tags:
            found_tags.append(keyword)
            if len(found_tags) >= max_tags:
                break

    # Find app keywords
    if len(found_tags) < max_tags:
        for keyword in app_keywords:
            if keyword in description_lower and keyword not in found_tags:
                found_tags.append(keyword)
                if len(found_tags) >= max_tags:
                    break

    return found_tags[:max_tags]


def categorize_activity(description: str, activity: str) -> str:
    """Categorize activity type from description and activity field.

    Args:
        description: Screenshot description
        activity: Activity field from AI

    Returns:
        Activity category
    """
    text = (description + " " + activity).lower()

    # Define activity categories
    if any(word in text for word in ["code", "coding", "programming", "debug", "develop", "git", "terminal"]):
        return "coding"
    elif any(word in text for word in ["browse", "web", "internet", "search", "article", "reading"]):
        return "browsing"
    elif any(word in text for word in ["design", "figma", "photoshop", "sketch", "illustrator"]):
        return "designing"
    elif any(word in text for word in ["write", "writing", "document", "doc", "note", "text"]):
        return "writing"
    elif any(word in text for word in ["email", "mail", "message", "chat", "slack", "communication"]):
        return "communication"
    elif any(word in text for word in ["video", "watch", "youtube", "meeting", "zoom", "conference"]):
        return "meeting"
    elif any(word in text for word in ["data", "database", "spreadsheet", "excel", "analysis"]):
        return "data"
    else:
        return "general"
