"""
Inverted Index implementation for efficient keyword lookup.
Maps keywords to documents that contain them with frequency information.
"""
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import re
from utils.stop_words import remove_stop_words

class InvertedIndex:
    """Inverted index data structure for fast keyword lookup."""
    
    def __init__(self, remove_stops: bool = True):
        """
        Initialize the inverted index.
        
        Args:
            remove_stops: Whether to remove stop words during indexing
        """
        # Map: keyword -> {doc_id: frequency}
        self.index: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.documents: Dict[str, str] = {}  # Map: doc_id -> content
        self.remove_stops = remove_stops
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize and normalize text."""
        # Convert to lowercase and split on non-alphanumeric characters
        tokens = re.findall(r'\b\w+\b', text.lower())
        
        # Remove stop words if enabled
        if self.remove_stops:
            tokens = remove_stop_words(tokens)
        
        return tokens
    
    def add_document(self, doc_id: str, content: str) -> None:
        """
        Add a document to the index.
        
        Args:
            doc_id: Unique identifier for the document
            content: Text content of the document
        """
        self.documents[doc_id] = content
        tokens = self._tokenize(content)
        
        # Count frequency of each token
        for token in tokens:
            self.index[token][doc_id] += 1
    
    def search(self, keyword: str) -> Dict[str, int]:
        """
        Search for documents containing a keyword.
        
        Args:
            keyword: Term to search for (case-insensitive)
        
        Returns:
            Dictionary mapping doc_id to frequency
        """
        normalized = keyword.lower()
        return dict(self.index.get(normalized, {}))
    
    def get_posting_list(self, keyword: str) -> Set[str]:
        """
        Get the posting list (set of doc IDs) for a keyword.
        
        Args:
            keyword: Term to search for
        
        Returns:
            Set of document IDs containing the keyword
        """
        normalized = keyword.lower()
        return set(self.index.get(normalized, {}).keys())
    
    def get_document(self, doc_id: str) -> str:
        """Get the content of a document."""
        return self.documents.get(doc_id, "")
    
    def get_all_keywords(self) -> Set[str]:
        """Get all indexed keywords."""
        return set(self.index.keys())
    
    def get_document_count(self) -> int:
        """Get total number of indexed documents."""
        return len(self.documents)
    
    def get_index_size(self) -> int:
        """Get total number of unique keywords."""
        return len(self.index)
