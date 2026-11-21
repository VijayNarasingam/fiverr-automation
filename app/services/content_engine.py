"""Content engine: Jinja2 templates + Ollama LLM enhancement for Fiverr gigs.

Consumes :class:`app.config.Settings` (``OLLAMA_BASE_URL``) and a row dict
from Google Sheets. Produces enhanced gig content with the fields
``title``, ``description``, ``faq_json``, ``tags`` and ``ab_variants``.

When Ollama is unavailable the engine falls back to template-only output so
the pipeline never stalls on a missing LLM.
"""

import logging
from pathlib import Path
from typing import Any

from jinja2 import Template

from app.config import settings
from app.services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


class ContentEngine:
    """Render Jinja2 templates and enhance gig content with Ollama."""

    def __init__(self, ollama: OllamaService | None = None):
        self.ollama = ollama or OllamaService()

    def render_template(self, template_name: str, **vars: Any) -> str:
        """Render *template_name* (a ``.j2`` file in ``app/templates``) with *vars*.

        Uses Jinja2 ``from_string`` semantics: the template file is read and
        compiled with :class:`jinja2.Template`, then rendered with *vars*.
        """
        template_path = TEMPLATES_DIR / f"{template_name}.j2"
        with open(template_path, "r", encoding="utf-8") as fh:
            source = fh.read()
        return Template(source).render(**vars)

    async def enhance_gig_content(self, row: dict) -> dict[str, Any]:
        """Produce enhanced gig content for a Sheets *row*.

        Combines template rendering with LLM enhancement. Fields returned:
        ``title``, ``description``, ``faq_json``, ``tags``, ``ab_variants``.

        If Ollama is unreachable or any LLM call fails, falls back to the
        template-rendered description with empty FAQs/tags.
        """
        title = row.get("title", row.get("Gig Title", "Untitled Gig"))
        category = row.get("category", row.get("Category", ""))
        price = row.get("price", row.get("Price", ""))
        raw_description = row.get("description", row.get("Description", ""))

        context = {
            "title": title,
            "category": category,
            "price": price,
            "description": raw_description,
            "row": row,
        }

        # Base description rendered from the Jinja2 template.
        rendered_description = self.render_template("gig_description", **context)

        description = rendered_description
        faq_json: list[dict[str, str]] = []
        tags: list[str] = []

        use_llm = await self.ollama.health_check()
        if use_llm:
            try:
                description = await self.ollama.polish_description(
                    rendered_description
                )
                faq_json = await self.ollama.generate_faq(row)
                tags = await self.ollama.suggest_tags(row)
            except Exception as exc:  # noqa: BLE001 — fall back gracefully
                logger.warning(
                    "Ollama enhancement failed, using template fallback: %s", exc
                )
                use_llm = False

        if not use_llm:
            description = rendered_description
            faq_json = []
            tags = tags or []

        ab_variants = [
            {
                "title": title,
                "description": description,
            },
            {
                "title": f"I will {title.strip().lower()}",
                "description": description,
            },
        ]

        return {
            "title": title,
            "description": description,
            "faq_json": faq_json,
            "tags": tags,
            "ab_variants": ab_variants,
        }
