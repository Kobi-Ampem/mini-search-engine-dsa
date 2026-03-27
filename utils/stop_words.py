# Stop words list for improved search accuracy
STOP_WORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
    'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'or', 'that',
    'the', 'to', 'was', 'will', 'with', 'would', 'this', 'but', 'if',
    'if', 'which', 'who', 'when', 'where', 'why', 'how', 'what', 'all',
    'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some',
    'such', 'no', 'nor', 'not', 'only', 'same', 'so', 'than', 'too',
    'very', 'just', 'can', 'could', 'should', 'may', 'might', 'must'
}

def is_stop_word(word: str) -> bool:
    """Check if a word is a stop word."""
    return word.lower() in STOP_WORDS

def remove_stop_words(words: list) -> list:
    """Remove stop words from a list of words."""
    return [word for word in words if not is_stop_word(word)]
