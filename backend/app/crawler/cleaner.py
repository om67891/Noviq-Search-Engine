import re

class Cleaner:
    """Cleans extracted content text deterministically."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Removes excessive whitespace, repeated newlines, and citation junk.
        """
        if not text:
            return ""
            
        # Remove Wikipedia style citations: [1], [2a], [citation needed]
        text = re.sub(r'\[\d+[a-z]?\]', '', text)
        text = re.sub(r'\[citation needed\]', '', text)
        
        # Remove common medical/science citation identifiers
        text = re.sub(r'PMID\s*\d+', '', text)
        text = re.sub(r'doi:10\.\d{4,9}/[-._;()/:A-Z0-9]+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'S2CID\s*\d+', '', text)
        text = re.sub(r'PMC\s*\d+', '', text)
        text = re.sub(r'Bibcode:[A-Za-z0-9.]+', '', text)
        
        # Remove Wikipedia upward arrows for references
        text = text.replace('↑', '')
        
        # Replace multiple spaces with a single space
        text = re.sub(r' +', ' ', text)
        
        # Replace 3 or more newlines with 2 newlines (paragraph break)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Strip leading and trailing whitespace
        return text.strip()
