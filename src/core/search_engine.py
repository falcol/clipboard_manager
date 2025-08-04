# ===============================================
# FILE: src/core/search_engine.py
# New advanced search engine
# ===============================================

"""
Advanced search engine for clipboard content
"""
import logging
from difflib import SequenceMatcher
from typing import Dict, List

from core.database import EnhancedClipboardDatabase

logger = logging.getLogger(__name__)


class SearchEngine:
    """Advanced search engine with multiple search strategies"""

    def __init__(self, database: EnhancedClipboardDatabase):
        self.database = database

    def search(self, query: str, limit: int = 25) -> List[Dict]:
        """
        Multi-strategy search with ranking
        Returns sorted results by relevance score
        """
        if not query or not query.strip():
            return self.database.get_items(limit=limit)

        query = query.strip().lower()

        # Get all items for searching
        all_items = self.database.get_items(limit=200)  # Search in larger set

        results = []

        for item in all_items:
            score = self._calculate_relevance_score(item, query)
            if score > 0:
                item["_search_score"] = score
                results.append(item)

        # Sort by relevance score (descending)
        results.sort(key=lambda x: x["_search_score"], reverse=True)

        return results[:limit]

    def _calculate_relevance_score(self, item: Dict, query: str) -> float:
        """Calculate relevance score for an item"""
        score = 0.0

        # Search in different fields with different weights
        search_fields = [
            (item.get("search_content", ""), 1.0),  # Main search content
            (item.get("preview", ""), 0.8),  # Preview text
            (str(item.get("metadata", {})), 0.3),  # Metadata
        ]

        for field_content, weight in search_fields:
            if not field_content:
                continue

            field_content = str(field_content).lower()

            # Exact match (highest score)
            if query in field_content:
                score += weight * 10

                # Bonus for exact phrase match at start
                if field_content.startswith(query):
                    score += weight * 5

            # Word-based matching
            query_words = query.split()
            field_words = field_content.split()

            for query_word in query_words:
                for field_word in field_words:
                    # Exact word match
                    if query_word == field_word:
                        score += weight * 3
                    # Partial word match
                    elif query_word in field_word or field_word in query_word:
                        score += weight * 1.5
                    # Fuzzy match
                    elif self._fuzzy_match(query_word, field_word):
                        score += weight * 1

        # Boost score for pinned items
        if item.get("is_pinned"):
            score *= 1.5

        # Boost score for recently accessed items
        access_count = item.get("access_count", 0)
        score += access_count * 0.1

        return score

    def _fuzzy_match(self, word1: str, word2: str, threshold: float = 0.8) -> bool:
        """Check if two words are similar using fuzzy matching"""
        if len(word1) < 3 or len(word2) < 3:
            return False

        similarity = SequenceMatcher(None, word1, word2).ratio()
        return similarity >= threshold

    def search_by_content_type(self, content_type: str, limit: int = 25) -> List[Dict]:
        """Search by specific content type"""
        try:
            if self.database.connection is None:
                logger.error("Database connection not initialized")
                return []

            cursor = self.database.connection.cursor()
            cursor.execute(
                """
                SELECT ci.*,
                       tc.content as text_content, tc.preview as text_preview,
                       ic.file_path, ic.thumbnail_path, ic.width, ic.height
                FROM clipboard_items ci
                LEFT JOIN text_content tc ON ci.id = tc.id
                LEFT JOIN image_content ic ON ci.id = ic.id
                WHERE ci.content_type = ?
                ORDER BY ci.is_pinned DESC, ci.timestamp DESC
                LIMIT ?
            """,
                (content_type, limit),
            )

            return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Error searching by content type: {e}")
            return []

    def search_by_date_range(
        self, start_date: str, end_date: str, limit: int = 25
    ) -> List[Dict]:
        """Search items within date range"""
        try:
            if self.database.connection is None:
                logger.error("Database connection not initialized")
                return []

            cursor = self.database.connection.cursor()
            cursor.execute(
                """
                SELECT ci.*,
                       tc.content as text_content, tc.preview as text_preview,
                       ic.file_path, ic.thumbnail_path, ic.width, ic.height
                FROM clipboard_items ci
                LEFT JOIN text_content tc ON ci.id = tc.id
                LEFT JOIN image_content ic ON ci.id = ic.id
                WHERE ci.timestamp BETWEEN ? AND ?
                ORDER BY ci.is_pinned DESC, ci.timestamp DESC
                LIMIT ?
            """,
                (start_date, end_date, limit),
            )

            return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Error searching by date range: {e}")
            return []

    def get_search_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """Get search suggestions based on partial query"""
        if len(partial_query) < 2:
            return []

        try:
            if self.database.connection is None:
                logger.error("Database connection not initialized")
                return []

            # Get unique search content that matches partial query
            cursor = self.database.connection.cursor()
            cursor.execute(
                """
                SELECT DISTINCT search_content
                FROM clipboard_items
                WHERE search_content LIKE ?
                ORDER BY access_count DESC, timestamp DESC
                LIMIT ?
            """,
                (f"%{partial_query.lower()}%", limit),
            )

            suggestions = []
            for row in cursor.fetchall():
                content = row["search_content"]
                # Extract relevant phrases from content
                words = content.split()
                for i, word in enumerate(words):
                    if partial_query.lower() in word.lower():
                        # Take a few words around the match
                        start = max(0, i - 1)
                        end = min(len(words), i + 3)
                        suggestion = " ".join(words[start:end])
                        if suggestion not in suggestions:
                            suggestions.append(suggestion)
                        break

            return suggestions[:limit]

        except Exception as e:
            logger.error(f"Error getting search suggestions: {e}")
            return []
