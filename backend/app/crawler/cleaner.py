import re

class Cleaner:
    """Cleans extracted content text deterministically."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Removes excessive whitespace and repeated newlines.
        """
        if not text:
            return ""
            
        # Replace multiple spaces with a single space
        text = re.sub(r' +', ' ', text)
        
        # Replace 3 or more newlines with 2 newlines (paragraph break)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Strip leading and trailing whitespace
        return text.strip()
