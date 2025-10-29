# app/services/citation_service.py
import re
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CitationService:
    """
    Service for extracting and formatting citations from research documents.
    
    Features:
    - Extract citations from reference sections
    - Parse APA, MLA, IEEE formats
    - Generate formatted citations
    - Detect in-text citations
    """

    def __init__(self):
        # Citation patterns for different formats
        self.patterns = {
            # APA: Author, A. A. (Year). Title. Journal, Volume(Issue), pages.
            'apa': r'([A-Z][a-zA-Z\s,&\.]+)\s*\((\d{4})\)\.\s*([^.]+)\.\s*([^,]+)',
            
            # MLA: Author. "Title." Journal Volume.Issue (Year): pages.
            'mla': r'([A-Z][a-zA-Z\s,\.]+)\.\s*"([^"]+)"\.\s*([^,]+)\s*(\d+)',
            
            # IEEE: [1] A. Author, "Title," Journal, vol. X, no. Y, pp. Z, Year.
            'ieee': r'\[(\d+)\]\s+([A-Z][a-zA-Z\s,\.]+),\s*"([^"]+)",\s*([^,]+)',
        }
        
        # Reference section headers
        self.ref_headers = [
            'references', 'bibliography', 'works cited', 'citations',
            'literature cited', 'reference list'
        ]

    # ==============================
    # MAIN EXTRACTION METHODS
    # ==============================

    def extract_citations(
        self,
        document_text: str,
        format_hint: Optional[str] = None
    ) -> List[Dict]:
        """
        Extract all citations from document text.
        
        Args:
            document_text: Full document text
            format_hint: Optional format hint ('apa', 'mla', 'ieee')
        
        Returns:
            List of citation dictionaries
        """
        logger.info("Extracting citations from document")
        
        # Step 1: Find reference section
        ref_section = self._find_references_section(document_text)
        
        if not ref_section:
            logger.warning("No reference section found")
            return []
        
        # Step 2: Extract citations based on format
        citations = []
        
        if format_hint:
            # Use specified format
            citations = self._parse_citations(ref_section, format_hint)
        else:
            # Try all formats and pick best match
            for fmt in ['apa', 'mla', 'ieee']:
                parsed = self._parse_citations(ref_section, fmt)
                if len(parsed) > len(citations):
                    citations = parsed
        
        logger.info(f"Extracted {len(citations)} citations")
        return citations

    def extract_in_text_citations(self, document_text: str) -> List[Dict]:
        """
        Extract in-text citations (e.g., "(Smith, 2020)" or "[1]")
        
        Returns:
            List of in-text citation references
        """
        in_text = []
        
        # Pattern for (Author, Year) style
        author_year_pattern = r'\(([A-Z][a-zA-Z\s&]+),\s*(\d{4})\)'
        matches = re.finditer(author_year_pattern, document_text)
        
        for match in matches:
            in_text.append({
                'type': 'author-year',
                'author': match.group(1).strip(),
                'year': match.group(2),
                'position': match.start()
            })
        
        # Pattern for [Number] style
        number_pattern = r'\[(\d+)\]'
        matches = re.finditer(number_pattern, document_text)
        
        for match in matches:
            in_text.append({
                'type': 'numbered',
                'number': match.group(1),
                'position': match.start()
            })
        
        logger.info(f"Found {len(in_text)} in-text citations")
        return in_text

    # ==============================
    # FORMATTING METHODS
    # ==============================

    def format_citation(
        self,
        citation_data: Dict,
        output_format: str = "apa"
    ) -> str:
        """
        Format citation data into specific citation style.
        
        Args:
            citation_data: Dict with keys: authors, year, title, journal, volume, pages
            output_format: 'apa', 'mla', or 'ieee'
        
        Returns:
            Formatted citation string
        """
        if output_format == "apa":
            return self._format_apa(citation_data)
        elif output_format == "mla":
            return self._format_mla(citation_data)
        elif output_format == "ieee":
            return self._format_ieee(citation_data)
        else:
            raise ValueError(f"Unknown citation format: {output_format}")

    def _format_apa(self, data: Dict) -> str:
        """
        Format as APA style:
        Author, A. A., & Author, B. B. (Year). Title of article. Title of Journal, volume(issue), pages.
        """
        authors = data.get('authors', 'Unknown Author')
        year = data.get('year', 'n.d.')
        title = data.get('title', 'Untitled')
        journal = data.get('journal', '')
        volume = data.get('volume', '')
        issue = data.get('issue', '')
        pages = data.get('pages', '')
        
        # Format authors (Last, F. M.)
        formatted_authors = self._format_authors_apa(authors)
        
        # Build citation
        citation = f"{formatted_authors} ({year}). {title}."
        
        if journal:
            citation += f" {journal}"
            if volume:
                citation += f", {volume}"
                if issue:
                    citation += f"({issue})"
            if pages:
                citation += f", {pages}"
            citation += "."
        
        return citation

    def _format_mla(self, data: Dict) -> str:
        """
        Format as MLA style:
        Author. "Title of Article." Title of Journal, vol. X, no. Y, Year, pp. Z-Z.
        """
        authors = data.get('authors', 'Unknown Author')
        year = data.get('year', 'n.d.')
        title = data.get('title', 'Untitled')
        journal = data.get('journal', '')
        volume = data.get('volume', '')
        issue = data.get('issue', '')
        pages = data.get('pages', '')
        
        # Format authors (Last, First)
        formatted_authors = self._format_authors_mla(authors)
        
        # Build citation
        citation = f'{formatted_authors}. "{title}."'
        
        if journal:
            citation += f" {journal}"
            if volume:
                citation += f", vol. {volume}"
            if issue:
                citation += f", no. {issue}"
            citation += f", {year}"
            if pages:
                citation += f", pp. {pages}"
            citation += "."
        
        return citation

    def _format_ieee(self, data: Dict) -> str:
        """
        Format as IEEE style:
        [1] A. Author and B. Author, "Title," Journal, vol. X, no. Y, pp. Z, Year.
        """
        authors = data.get('authors', 'Unknown Author')
        year = data.get('year', 'n.d.')
        title = data.get('title', 'Untitled')
        journal = data.get('journal', '')
        volume = data.get('volume', '')
        issue = data.get('issue', '')
        pages = data.get('pages', '')
        number = data.get('number', '1')
        
        # Format authors (F. Last)
        formatted_authors = self._format_authors_ieee(authors)
        
        # Build citation
        citation = f'[{number}] {formatted_authors}, "{title}"'
        
        if journal:
            citation += f", {journal}"
            if volume:
                citation += f", vol. {volume}"
            if issue:
                citation += f", no. {issue}"
            if pages:
                citation += f", pp. {pages}"
            citation += f", {year}."
        
        return citation

    # ==============================
    # HELPER METHODS
    # ==============================

    def _find_references_section(self, text: str) -> Optional[str]:
        """
        Find and extract the references/bibliography section from document text.
        """
        text_lower = text.lower()
        
        for header in self.ref_headers:
            # Look for section header
            pattern = rf'\n\s*{header}\s*\n'
            match = re.search(pattern, text_lower)
            
            if match:
                # Extract everything after the header
                start_pos = match.end()
                
                # Try to find end of references (next major section or end of doc)
                end_pattern = r'\n\s*(appendix|acknowledgments?|figures?|tables?)\s*\n'
                end_match = re.search(end_pattern, text_lower[start_pos:])
                
                if end_match:
                    end_pos = start_pos + end_match.start()
                    return text[start_pos:end_pos]
                else:
                    # Return rest of document
                    return text[start_pos:]
        
        logger.warning("Reference section not found")
        return None

    def _parse_citations(self, ref_text: str, format_type: str) -> List[Dict]:
        """
        Parse citations from reference text based on format.
        """
        citations = []
        pattern = self.patterns.get(format_type)
        
        if not pattern:
            return citations
        
        # Split into individual citations (usually one per line)
        lines = ref_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if len(line) < 20:  # Skip short lines
                continue
            
            match = re.search(pattern, line)
            if match:
                citation = self._extract_citation_data(match, format_type, line)
                if citation:
                    citations.append(citation)
        
        return citations

    def _extract_citation_data(self, match, format_type: str, full_line: str) -> Dict:
        """
        Extract structured data from regex match.
        """
        try:
            if format_type == 'apa':
                return {
                    'format': 'APA',
                    'authors': match.group(1).strip(),
                    'year': match.group(2),
                    'title': match.group(3).strip(),
                    'journal': match.group(4).strip() if len(match.groups()) > 3 else '',
                    'raw_text': full_line
                }
            elif format_type == 'mla':
                return {
                    'format': 'MLA',
                    'authors': match.group(1).strip(),
                    'title': match.group(2).strip(),
                    'journal': match.group(3).strip(),
                    'year': match.group(4),
                    'raw_text': full_line
                }
            elif format_type == 'ieee':
                return {
                    'format': 'IEEE',
                    'number': match.group(1),
                    'authors': match.group(2).strip(),
                    'title': match.group(3).strip(),
                    'journal': match.group(4).strip(),
                    'raw_text': full_line
                }
        except Exception as e:
            logger.error(f"Error extracting citation data: {e}")
            return None

    def _format_authors_apa(self, authors: str) -> str:
        """Format authors for APA: Last, F. M., & Last, F. M."""
        # Simple implementation - can be enhanced
        authors = authors.replace(' and ', ', & ')
        return authors

    def _format_authors_mla(self, authors: str) -> str:
        """Format authors for MLA: Last, First"""
        return authors

    def _format_authors_ieee(self, authors: str) -> str:
        """Format authors for IEEE: F. Last and F. Last"""
        authors = authors.replace(',', ' and')
        return authors

    def _extract_year(self, text: str) -> Optional[str]:
        """Extract year from citation text."""
        year_match = re.search(r'\b(19|20)\d{2}\b', text)
        return year_match.group(0) if year_match else None

    def _extract_authors(self, text: str) -> str:
        """Extract author names from citation text."""
        # Look for pattern before year
        author_match = re.search(r'^([A-Z][^(]+)\s*\(', text)
        return author_match.group(1).strip() if author_match else "Unknown"

    # ==============================
    # BATCH OPERATIONS
    # ==============================

    def generate_bibliography(
        self,
        citations: List[Dict],
        format_type: str = "apa",
        sort_by: str = "author"
    ) -> str:
        """
        Generate a formatted bibliography from citations.
        
        Args:
            citations: List of citation dictionaries
            format_type: Output format ('apa', 'mla', 'ieee')
            sort_by: Sort order ('author', 'year', 'title')
        
        Returns:
            Formatted bibliography string
        """
        # Sort citations
        if sort_by == "author":
            citations.sort(key=lambda x: x.get('authors', ''))
        elif sort_by == "year":
            citations.sort(key=lambda x: x.get('year', ''), reverse=True)
        elif sort_by == "title":
            citations.sort(key=lambda x: x.get('title', ''))
        
        # Format each citation
        bibliography = []
        for i, citation in enumerate(citations, 1):
            if format_type == 'ieee':
                citation['number'] = str(i)
            
            formatted = self.format_citation(citation, format_type)
            bibliography.append(formatted)
        
        return '\n\n'.join(bibliography)

    def validate_citation(self, citation: Dict) -> Dict:
        """
        Validate citation has required fields.
        
        Returns:
            Dict with 'valid' bool and 'missing_fields' list
        """
        required_fields = ['authors', 'year', 'title']
        missing = [field for field in required_fields if not citation.get(field)]
        
        return {
            'valid': len(missing) == 0,
            'missing_fields': missing,
            'warnings': self._check_citation_warnings(citation)
        }

    def _check_citation_warnings(self, citation: Dict) -> List[str]:
        """Check for potential citation issues."""
        warnings = []
        
        # Check year format
        year = citation.get('year', '')
        if year and not re.match(r'^\d{4}$', str(year)):
            warnings.append(f"Unusual year format: {year}")
        
        # Check for missing journal info
        if not citation.get('journal'):
            warnings.append("Missing journal/publication information")
        
        # Check author format
        authors = citation.get('authors', '')
        if authors and not re.search(r'[A-Z]', authors):
            warnings.append("Authors may not be properly capitalized")
        
        return warnings