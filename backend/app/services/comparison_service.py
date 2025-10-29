# app/services/comparison_service.py
import logging
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.document_service import DocumentService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class ComparisonService:
    """
    Service for comparing multiple research documents.
    
    Features:
    - Extract key findings from multiple papers
    - Compare methodologies
    - Identify agreements and contradictions
    - Generate comparison tables
    - Detect trends across documents
    """

    def __init__(self, db: AsyncSession, llm_service: LLMService):
        self.db = db
        self.llm_service = llm_service
        self.doc_service = DocumentService(db)

    # ==============================
    # MAIN COMPARISON METHODS
    # ==============================

    async def compare_documents(
        self,
        document_ids: List[str],
        comparison_aspects: List[str] = None,
        include_contradictions: bool = True
    ) -> Dict:
        """
        Compare multiple documents and generate comprehensive comparison report.
        
        Args:
            document_ids: List of document IDs to compare (2-10 documents)
            comparison_aspects: Specific aspects to compare (e.g., ['methodology', 'results'])
            include_contradictions: Whether to identify contradictions
        
        Returns:
            Comprehensive comparison dictionary
        """
        if len(document_ids) < 2:
            raise ValueError("Need at least 2 documents for comparison")
        
        if len(document_ids) > 10:
            raise ValueError("Maximum 10 documents for comparison")
        
        logger.info(f"Comparing {len(document_ids)} documents")
        
        # Step 1: Extract key findings from each document
        document_summaries = await self._extract_document_summaries(document_ids)
        
        # Step 2: Compare specific aspects
        if not comparison_aspects:
            comparison_aspects = ['objectives', 'methodology', 'findings', 'conclusions']
        
        aspect_comparisons = {}
        for aspect in comparison_aspects:
            aspect_comparisons[aspect] = await self._compare_aspect(
                document_summaries, aspect
            )
        
        # Step 3: Identify agreements and contradictions
        agreements_contradictions = None
        if include_contradictions:
            agreements_contradictions = await self._find_agreements_contradictions(
                document_summaries
            )
        
        # Step 4: Generate comparison table
        comparison_table = await self._generate_comparison_table(
            document_summaries, comparison_aspects
        )
        
        # Step 5: Detect trends
        trends = await self._detect_trends(document_summaries)
        
        return {
            'total_documents': len(document_ids),
            'document_summaries': document_summaries,
            'aspect_comparisons': aspect_comparisons,
            'agreements_contradictions': agreements_contradictions,
            'comparison_table': comparison_table,
            'trends': trends,
            'overall_synthesis': await self._generate_synthesis(document_summaries)
        }

    async def generate_comparison_table(
        self,
        document_ids: List[str],
        columns: List[str] = None
    ) -> Dict:
        """
        Generate a side-by-side comparison table.
        
        Args:
            document_ids: List of document IDs
            columns: Table columns (aspects to compare)
        
        Returns:
            Structured comparison table
        """
        if not columns:
            columns = ['Title', 'Year', 'Methodology', 'Key Findings', 'Sample Size', 'Limitations']
        
        logger.info(f"Generating comparison table for {len(document_ids)} documents")
        
        # Extract information for each document
        table_data = []
        
        for doc_id in document_ids:
            # Get document metadata
            doc = await self.doc_service.get_document(doc_id, user_id="system")
            
            if not doc:
                continue
            
            # Extract relevant chunks for analysis
            doc_chunks = await self.doc_service.search_similar_chunks(
                query="methodology findings results conclusions",
                doc_ids=[doc_id],
                top_k=10
            )
            
            doc_content = "\n".join(doc_chunks)
            
            # Extract information for each column
            row_data = {'document_id': doc_id, 'document_name': doc.name}
            
            for column in columns:
                value = await self._extract_column_value(doc_content, column)
                row_data[column] = value
            
            table_data.append(row_data)
        
        return {
            'columns': ['Document'] + columns,
            'rows': table_data,
            'document_count': len(table_data)
        }

    # ==============================
    # EXTRACTION METHODS
    # ==============================

    async def _extract_document_summaries(self, document_ids: List[str]) -> List[Dict]:
        """
        Extract structured summaries from each document.
        """
        summaries = []
        
        for doc_id in document_ids:
            try:
                # Get document
                doc = await self.doc_service.get_document(doc_id, user_id="system")
                
                if not doc:
                    logger.warning(f"Document {doc_id} not found")
                    continue
                
                # Get document chunks
                chunks = await self.doc_service.search_similar_chunks(
                    query="main findings methodology results conclusions",
                    doc_ids=[doc_id],
                    top_k=15
                )
                
                doc_content = "\n\n".join(chunks)
                
                # Extract structured information using LLM
                summary = await self._extract_structured_summary(doc_content, doc.name)
                summary['document_id'] = doc_id
                summary['document_name'] = doc.name
                
                summaries.append(summary)
                
            except Exception as e:
                logger.error(f"Error extracting summary for {doc_id}: {e}")
                continue
        
        return summaries

    async def _extract_structured_summary(self, content: str, doc_name: str) -> Dict:
        """
        Extract structured information from document content using LLM.
        """
        prompt = f"""Analyze this research document and extract the following information in a structured format:

Document: {doc_name}

Content:
{content[:3000]}

Please provide:
1. Main objective/research question
2. Methodology used
3. Key findings (3-5 points)
4. Sample size or data used
5. Main conclusions
6. Limitations mentioned
7. Year of publication (if mentioned)

Format your response as clear sections with bullet points."""
        
        # Use Gemma for analytical tasks
        response = await self.llm_service.generate_response(
            prompt_name="research_insight",
            content=content,
            model_name="gemma",
            max_tokens=800
        )
        
        # Parse response into structured format
        return self._parse_structured_response(response, doc_name)

    def _parse_structured_response(self, response: str, doc_name: str) -> Dict:
        """
        Parse LLM response into structured dictionary.
        """
        # Simple parsing - can be enhanced with better NLP
        sections = {
            'objective': '',
            'methodology': '',
            'findings': [],
            'sample_size': '',
            'conclusions': '',
            'limitations': '',
            'year': ''
        }
        
        # Extract sections from response
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            line_lower = line.lower()
            
            if 'objective' in line_lower or 'research question' in line_lower:
                current_section = 'objective'
            elif 'methodology' in line_lower or 'method' in line_lower:
                current_section = 'methodology'
            elif 'finding' in line_lower or 'result' in line_lower:
                current_section = 'findings'
            elif 'sample' in line_lower:
                current_section = 'sample_size'
            elif 'conclusion' in line_lower:
                current_section = 'conclusions'
            elif 'limitation' in line_lower:
                current_section = 'limitations'
            elif 'year' in line_lower:
                current_section = 'year'
            elif current_section and line.startswith('-'):
                # Bullet point
                if current_section == 'findings':
                    sections['findings'].append(line[1:].strip())
                else:
                    sections[current_section] += line[1:].strip() + ' '
            elif current_section:
                sections[current_section] += line + ' '
        
        # Clean up
        for key in sections:
            if isinstance(sections[key], str):
                sections[key] = sections[key].strip()
        
        return sections

    async def _extract_column_value(self, content: str, column: str) -> str:
        """
        Extract specific column value from document content.
        """
        prompt = f"""From the following research document, extract the {column}. Be concise and specific.

Content:
{content[:2000]}

{column}:"""
        
        response = await self.llm_service.generate_response(
            prompt_name="conversation",
            content=prompt,
            model_name="gemma",
            max_tokens=200
        )
        
        return response.strip()

    # ==============================
    # COMPARISON ANALYSIS METHODS
    # ==============================

    async def _compare_aspect(
        self,
        document_summaries: List[Dict],
        aspect: str
    ) -> Dict:
        """
        Compare a specific aspect across all documents.
        """
        # Collect aspect data from all documents
        aspect_data = []
        for summary in document_summaries:
            aspect_value = summary.get(aspect, 'Not specified')
            aspect_data.append({
                'document': summary.get('document_name', 'Unknown'),
                'value': aspect_value
            })
        
        # Generate comparison using LLM
        comparison_prompt = f"""Compare the {aspect} across these research documents:

"""
        for i, data in enumerate(aspect_data, 1):
            comparison_prompt += f"\n{i}. {data['document']}: {data['value']}"
        
        comparison_prompt += f"\n\nProvide a comparative analysis of the {aspect} across these documents. Highlight similarities, differences, and notable patterns."
        
        comparison_text = await self.llm_service.generate_response(
            prompt_name="conversation",
            content=comparison_prompt,
            model_name="gemma",
            max_tokens=500
        )
        
        return {
            'aspect': aspect,
            'data': aspect_data,
            'analysis': comparison_text
        }

    async def _find_agreements_contradictions(
        self,
        document_summaries: List[Dict]
    ) -> Dict:
        """
        Identify agreements and contradictions across documents.
        """
        # Prepare content for analysis
        findings_text = ""
        for i, summary in enumerate(document_summaries, 1):
            findings = summary.get('findings', [])
            if isinstance(findings, list):
                findings_str = '\n  - '.join(findings)
            else:
                findings_str = findings
            
            findings_text += f"\nDocument {i} ({summary.get('document_name', 'Unknown')}):\n  - {findings_str}\n"
        
        # Use LLM to identify agreements/contradictions
        prompt = f"""Analyze the following research findings from multiple documents and identify:
1. KEY AGREEMENTS: Findings that are consistent across studies
2. CONTRADICTIONS: Findings that conflict between studies
3. UNIQUE CONTRIBUTIONS: Novel findings from individual studies

Findings:
{findings_text}

Provide a structured analysis with clear sections for agreements, contradictions, and unique contributions."""
        
        analysis = await self.llm_service.generate_response(
            prompt_name="conversation",
            content=prompt,
            model_name="gemma",
            max_tokens=1000
        )
        
        return {
            'analysis': analysis,
            'document_count': len(document_summaries)
        }

    async def _generate_comparison_table(
        self,
        document_summaries: List[Dict],
        aspects: List[str]
    ) -> Dict:
        """
        Generate structured comparison table.
        """
        table = {
            'headers': ['Document'] + aspects,
            'rows': []
        }
        
        for summary in document_summaries:
            row = [summary.get('document_name', 'Unknown')]
            
            for aspect in aspects:
                value = summary.get(aspect, 'Not specified')
                if isinstance(value, list):
                    value = '; '.join(value[:3])  # First 3 items
                row.append(str(value)[:100])  # Truncate to 100 chars
            
            table['rows'].append(row)
        
        return table

    async def _detect_trends(self, document_summaries: List[Dict]) -> Dict:
        """
        Detect trends across documents (e.g., methodological trends, evolving findings).
        """
        # Extract years if available
        years = [s.get('year', '') for s in document_summaries if s.get('year')]
        
        # Prepare trend analysis prompt
        methodologies = [s.get('methodology', 'N/A') for s in document_summaries]
        
        prompt = f"""Analyze trends across these {len(document_summaries)} research documents:

Years: {', '.join(years) if years else 'Not specified'}

Methodologies used:
{chr(10).join(f"{i+1}. {m}" for i, m in enumerate(methodologies))}

Identify:
1. Methodological trends (changes in research approaches over time)
2. Evolving findings (how results have progressed)
3. Emerging themes or focus areas
4. Any temporal patterns

Provide a concise trend analysis."""
        
        trend_analysis = await self.llm_service.generate_response(
            prompt_name="conversation",
            content=prompt,
            model_name="gemma",
            max_tokens=600
        )
        
        return {
            'analysis': trend_analysis,
            'timeline': sorted(years) if years else [],
            'methodology_evolution': methodologies
        }

    async def _generate_synthesis(self, document_summaries: List[Dict]) -> str:
        """
        Generate overall synthesis/meta-analysis of all documents.
        """
        synthesis_prompt = f"""Provide a comprehensive synthesis of these {len(document_summaries)} research documents:

"""
        for i, summary in enumerate(document_summaries, 1):
            synthesis_prompt += f"\n{i}. {summary.get('document_name', 'Unknown')}"
            synthesis_prompt += f"\n   Objective: {summary.get('objective', 'N/A')}"
            synthesis_prompt += f"\n   Key Findings: {', '.join(summary.get('findings', ['N/A'])[:3])}"
        
        synthesis_prompt += """\n\nProvide:
1. Overall state of research in this area
2. Collective insights from these studies
3. Research gaps identified
4. Future research directions suggested by these works"""
        
        synthesis = await self.llm_service.generate_response(
            prompt_name="conversation",
            content=synthesis_prompt,
            model_name="gemma",
            max_tokens=800
        )
        
        return synthesis

    # ==============================
    # SPECIALIZED COMPARISON METHODS
    # ==============================

    async def compare_methodologies(self, document_ids: List[str]) -> Dict:
        """
        Focused comparison of research methodologies.
        """
        summaries = await self._extract_document_summaries(document_ids)
        
        methodologies = []
        for summary in summaries:
            methodologies.append({
                'document': summary.get('document_name', 'Unknown'),
                'methodology': summary.get('methodology', 'Not specified'),
                'sample_size': summary.get('sample_size', 'Not specified')
            })
        
        # Generate comparison
        prompt = "Compare the research methodologies:\n\n"
        for m in methodologies:
            prompt += f"- {m['document']}: {m['methodology']}\n"
        
        prompt += "\nAnalyze: 1) Methodological similarities 2) Differences in approach 3) Strengths/weaknesses"
        
        analysis = await self.llm_service.generate_response(
            prompt_name="conversation",
            content=prompt,
            model_name="gemma",
            max_tokens=600
        )
        
        return {
            'methodologies': methodologies,
            'analysis': analysis
        }

    async def identify_research_gaps(self, document_ids: List[str]) -> Dict:
        """
        Identify research gaps across multiple papers.
        """
        summaries = await self._extract_document_summaries(document_ids)
        
        # Collect limitations and conclusions
        limitations_text = ""
        for summary in summaries:
            doc_name = summary.get('document_name', 'Unknown')
            limitations = summary.get('limitations', 'Not specified')
            limitations_text += f"\n{doc_name}: {limitations}\n"
        
        prompt = f"""Based on these research papers' limitations and conclusions:

{limitations_text}

Identify:
1. Research gaps that multiple papers acknowledge
2. Unexplored areas or questions
3. Methodological improvements needed
4. Suggested future research directions"""
        
        gaps_analysis = await self.llm_service.generate_response(
            prompt_name="conversation",
            content=prompt,
            model_name="gemma",
            max_tokens=700
        )
        
        return {
            'analysis': gaps_analysis,
            'document_count': len(summaries)
        }

    async def generate_meta_summary(
        self,
        document_ids: List[str],
        summary_type: str = "comprehensive"
    ) -> str:
        """
        Generate a meta-summary across all documents.
        
        Args:
            document_ids: List of document IDs
            summary_type: "brief", "comprehensive", or "executive"
        
        Returns:
            Meta-summary string
        """
        summaries = await self._extract_document_summaries(document_ids)
        
        if summary_type == "brief":
            max_tokens = 300
            instruction = "Provide a brief 3-paragraph summary"
        elif summary_type == "executive":
            max_tokens = 500
            instruction = "Provide an executive summary with key takeaways"
        else:  # comprehensive
            max_tokens = 1000
            instruction = "Provide a comprehensive summary covering all major themes"
        
        # Prepare content
        content = f"Meta-analysis of {len(document_ids)} research documents:\n\n"
        for i, summary in enumerate(summaries, 1):
            content += f"{i}. {summary.get('document_name', 'Unknown')}\n"
            content += f"   Findings: {', '.join(summary.get('findings', ['N/A'])[:3])}\n\n"
        
        prompt = f"""{content}

{instruction} that synthesizes the collective insights from these papers."""
        
        meta_summary = await self.llm_service.generate_response(
            prompt_name="conversation",
            content=prompt,
            model_name="gemma",
            max_tokens=max_tokens
        )
        
        return meta_summary

    # ==============================
    # VISUALIZATION HELPERS
    # ==============================

    async def generate_comparison_matrix(self, document_ids: List[str]) -> Dict:
        """
        Generate a comparison matrix showing document similarities.
        Returns matrix suitable for heatmap visualization.
        """
        summaries = await self._extract_document_summaries(document_ids)
        n = len(summaries)
        
        # Initialize similarity matrix
        matrix = [[0 for _ in range(n)] for _ in range(n)]
        
        # Calculate pairwise similarities (simplified)
        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i][j] = 1.0
                else:
                    # Simple keyword-based similarity
                    doc1_text = ' '.join(summaries[i].get('findings', []))
                    doc2_text = ' '.join(summaries[j].get('findings', []))
                    
                    # Count common words (simple approach)
                    words1 = set(doc1_text.lower().split())
                    words2 = set(doc2_text.lower().split())
                    
                    common = len(words1.intersection(words2))
                    total = len(words1.union(words2))
                    
                    matrix[i][j] = common / total if total > 0 else 0
        
        return {
            'matrix': matrix,
            'labels': [s.get('document_name', f'Doc {i+1}') for i, s in enumerate(summaries)],
            'size': n
        }

    async def generate_timeline_data(self, document_ids: List[str]) -> Dict:
        """
        Generate timeline data for documents (if years are available).
        """
        summaries = await self._extract_document_summaries(document_ids)
        
        timeline = []
        for summary in summaries:
            year = summary.get('year', '')
            if year:
                try:
                    year_int = int(year)
                    timeline.append({
                        'year': year_int,
                        'document': summary.get('document_name', 'Unknown'),
                        'key_finding': summary.get('findings', ['N/A'])[0] if summary.get('findings') else 'N/A'
                    })
                except ValueError:
                    continue
        
        # Sort by year
        timeline.sort(key=lambda x: x['year'])
        
        return {
            'timeline': timeline,
            'year_range': (timeline[0]['year'], timeline[-1]['year']) if timeline else (None, None),
            'document_count': len(timeline)
        }