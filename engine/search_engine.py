"""
Main search engine with boolean queries, ranking, and snippet generation.
"""
import re
import time
from typing import Dict, List, Set, Tuple, Optional
from collections import Counter
from engine.inverted_index import InvertedIndex

class SearchEngine:
    """Search engine with boolean operations, ranking, and snippet preview."""
    
    def __init__(self, remove_stop_words: bool = True):
        """Initialize the search engine."""
        self.index = InvertedIndex(remove_stops=remove_stop_words)
        self.last_search_time = 0
    
    def add_document(self, doc_id: str, content: str) -> None:
        """Add a document to the search engine."""
        self.index.add_document(doc_id, content)
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words."""
        return re.findall(r'\b\w+\b', text.lower())
    
    def _calculate_relevance(self, doc_id: str, keywords: List[str]) -> float:
        """
        Calculate relevance score based on keyword frequency and coverage.
        
        Args:
            doc_id: Document ID
            keywords: List of search keywords
        
        Returns:
            Relevance score
        """
        score = 0.0
        content = self.index.get_document(doc_id)
        
        # Score based on frequency of keywords
        for keyword in keywords:
            freq = self.index.search(keyword).get(doc_id, 0)
            score += freq
        
        # Bonus for having multiple keywords
        matching_keywords = sum(1 for kw in keywords if doc_id in self.index.get_posting_list(kw))
        score *= (1 + matching_keywords * 0.1)
        
        return score
    
    def _generate_snippet(self, text: str, keywords: List[str], snippet_length: int = 150) -> str:
        """
        Generate a snippet of text with keywords highlighted.
        
        Args:
            text: Full text content
            keywords: Keywords to highlight
            snippet_length: Max length of snippet
        
        Returns:
            Snippet with highlighted keywords
        """
        # Find first occurrence of any keyword
        text_lower = text.lower()
        first_pos = len(text)
        
        for keyword in keywords:
            pos = text_lower.find(keyword.lower())
            if pos != -1 and pos < first_pos:
                first_pos = pos
        
        # Extract snippet around first keyword occurrence
        if first_pos == len(text):
            # No keyword found, take beginning
            start = 0
        else:
            start = max(0, first_pos - 50)
        
        end = min(len(text), start + snippet_length)
        snippet = text[start:end]
        
        # Add ellipsis if truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        
        # Highlight keywords in snippet
        highlighted = snippet
        for keyword in keywords:
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            highlighted = pattern.sub(f"**{keyword}**", highlighted)
        
        return highlighted
    
    def search_simple(self, query: str, top_k: int = 5) -> List[Tuple[str, float, str]]:
        """
        Simple multi-keyword search with ranking.
        
        Args:
            query: Search query (space-separated keywords)
            top_k: Number of top results to return
        
        Returns:
            List of (doc_id, score, snippet) tuples, sorted by relevance
        """
        start_time = time.time()
        
        # Parse keywords and filter stops if needed
        keywords = self._tokenize(query)
        
        if not keywords:
            self.last_search_time = time.time() - start_time
            return []
        
        # Find documents containing any keyword
        doc_scores: Dict[str, float] = {}
        
        for keyword in keywords:
            posting_list = self.index.get_posting_list(keyword)
            for doc_id in posting_list:
                if doc_id not in doc_scores:
                    doc_scores[doc_id] = 0
                
                # Add frequency-based score
                freq = self.index.search(keyword).get(doc_id, 0)
                doc_scores[doc_id] += freq
        
        # Rank by relevance
        ranked = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        # Generate snippets
        results = []
        for doc_id, score in ranked:
            content = self.index.get_document(doc_id)
            snippet = self._generate_snippet(content, keywords)
            results.append((doc_id, score, snippet))
        
        self.last_search_time = time.time() - start_time
        return results
    
    def search_boolean(self, query: str, top_k: int = 5) -> List[Tuple[str, float, str]]:
        """
        Boolean search supporting AND, OR, NOT operators.
        
        Args:
            query: Boolean query (e.g., "python AND tutorial NOT beginner")
            top_k: Number of top results to return
        
        Returns:
            List of (doc_id, score, snippet) tuples
        """
        start_time = time.time()
        
        # Parse boolean query
        and_groups = query.split(' AND ')
        or_groups = [g.split(' OR ') for g in and_groups]
        
        # Extract keywords and NOT terms
        all_keywords = []
        not_keywords = set()
        
        for or_group in or_groups:
            for term in or_group:
                if ' NOT ' in term:
                    parts = term.split(' NOT ')
                    keyword = self._tokenize(parts[0])[0] if self._tokenize(parts[0]) else ""
                    not_term = self._tokenize(parts[1])[0] if self._tokenize(parts[1]) else ""
                    if keyword:
                        all_keywords.append(keyword)
                    if not_term:
                        not_keywords.add(not_term)
                else:
                    tokens = self._tokenize(term)
                    if tokens:
                        all_keywords.append(tokens[0])
        
        # Process AND/OR logic
        result_docs = None
        and_groups = query.split(' AND ')
        
        for and_term in and_groups:
            or_docs = set()
            or_parts = and_term.split(' OR ')
            
            for or_part in or_parts:
                # Remove NOT operators for initial search
                clean_part = or_part.split(' NOT ')[0].strip()
                tokens = self._tokenize(clean_part)
                
                if tokens:
                    keyword = tokens[0]
                    or_docs.update(self.index.get_posting_list(keyword))
            
            if result_docs is None:
                result_docs = or_docs
            else:
                result_docs = result_docs.intersection(or_docs)
        
        # Apply NOT filter
        if not_keywords:
            not_docs = set()
            for not_keyword in not_keywords:
                not_docs.update(self.index.get_posting_list(not_keyword))
            if result_docs:
                result_docs = result_docs - not_docs
        
        # Rank documents
        result_docs = result_docs or set()
        doc_scores = {doc_id: self._calculate_relevance(doc_id, all_keywords) 
                     for doc_id in result_docs}
        
        ranked = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        # Generate results with snippets
        results = []
        for doc_id, score in ranked:
            content = self.index.get_document(doc_id)
            snippet = self._generate_snippet(content, all_keywords)
            results.append((doc_id, score, snippet))
        
        self.last_search_time = time.time() - start_time
        return results
    
    def get_search_time(self) -> float:
        """Get the execution time of the last search in milliseconds."""
        return self.last_search_time * 1000
    
    def get_statistics(self) -> Dict:
        """Get index statistics."""
        return {
            'total_documents': self.index.get_document_count(),
            'total_keywords': self.index.get_index_size(),
            'last_search_time_ms': self.get_search_time()
        }
