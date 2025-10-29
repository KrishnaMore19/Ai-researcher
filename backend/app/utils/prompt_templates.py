# app/utils/prompt_templates.py
"""
prompt_templates.py - Centralized repository for reusable prompt templates
used by LLM and embedding services across the app.

NEW: UPDATED with advanced summarization and comparison templates
"""

from typing import Dict


# -------------------------------
# DOCUMENT PROMPTS
# -------------------------------

DOCUMENT_SUMMARY_PROMPT = """
You are an AI assistant that summarizes research or technical documents.
Summarize the following content clearly and concisely:
---
{content}
---
Return a professional summary within 200 words.
"""

DOCUMENT_ANALYSIS_PROMPT = """
You are an expert research analyst. Analyze the document below and provide:
1. Key insights
2. Limitations
3. Actionable takeaways
---
{content}
---
Respond in bullet points.
"""

# NEW: Advanced Summarization Templates

SUMMARY_SHORT = """
Provide a concise 3-5 sentence summary focusing on the most important points:

{content}

Summary:"""

SUMMARY_DETAILED = """
Provide a comprehensive summary including:
1. **Main Objective/Purpose**: What problem or question does this address?
2. **Methodology/Approach**: How was the research conducted or problem approached?
3. **Key Findings/Results**: What were the main discoveries or outcomes?
4. **Conclusions**: What do the authors conclude?
5. **Limitations**: Any noted limitations or constraints?

Document content:
{content}

Detailed Summary:"""

SUMMARY_BULLET = """
Summarize the following document as clear, concise bullet points. Focus on:
- Main topics and themes
- Key findings or arguments
- Important data or statistics
- Conclusions or recommendations

Document:
{content}

Bullet Point Summary:
•"""

SUMMARY_SECTION = """
Break down this document into sections with summaries for each:

**Document Structure:**
# Introduction / Background
# Methods / Approach  
# Key Findings / Results
# Discussion / Analysis
# Conclusions / Future Work

Document content:
{content}

Section-wise Breakdown:"""

# -------------------------------
# CHAT / CONVERSATION PROMPTS
# -------------------------------

CONVERSATION_PROMPT = """
You are a friendly and knowledgeable AI research assistant.
Respond to the user's query conversationally, while maintaining accuracy and professionalism.

User query:
---
{query}
---

Context from documents (if available):
{context}

Provide a helpful, accurate response based on the context provided. If the context doesn't contain relevant information, acknowledge this and provide what general knowledge you can."""

FOLLOW_UP_PROMPT = """
Generate 3 short, contextually relevant follow-up questions the user might ask
based on the conversation so far:
---
{conversation_history}
---
Return as a simple numbered list.
"""

# NEW: Comparison Prompts

COMPARISON_DOCUMENTS = """
You are an expert at comparing research documents. Compare the following documents across these aspects:
{aspects}

Documents:
{documents}

Provide a structured comparison highlighting:
1. Similarities between the documents
2. Key differences in approach or findings
3. Unique contributions from each document
4. Overall patterns or trends

Comparison Analysis:"""

COMPARISON_METHODOLOGIES = """
Compare the research methodologies used in these studies:

{methodologies}

Analyze:
1. **Methodological Similarities**: What approaches do they share?
2. **Differences in Design**: How do their methods differ?
3. **Strengths and Limitations**: Evaluate each methodology
4. **Best Practices**: Which approaches seem most effective?

Methodology Comparison:"""

IDENTIFY_CONTRADICTIONS = """
Analyze the following research findings and identify agreements and contradictions:

{findings}

Provide:
1. **Key Agreements**: Findings that are consistent across studies
2. **Contradictions**: Conflicting results or conclusions
3. **Possible Explanations**: Why might these contradictions exist?
4. **Implications**: What do these agreements/contradictions mean for the field?

Analysis:"""

# -------------------------------
# ANALYTICS / INSIGHTS PROMPTS
# -------------------------------

RESEARCH_INSIGHT_PROMPT = """
You are a data-driven AI that extracts research insights.
From the following notes or paper content, list:
- Main research problem
- Methodology summary
- Key results
- Future work direction
---
{content}
"""

# NEW: Trend Analysis

TREND_ANALYSIS = """
Analyze trends across these research documents published over time:

Timeline: {timeline}

Documents:
{documents}

Identify:
1. **Methodological Evolution**: How have research methods changed?
2. **Shifting Focus**: What topics have gained/lost attention?
3. **Emerging Themes**: What new ideas are appearing?
4. **Knowledge Progression**: How has understanding evolved?

Trend Analysis:"""

RESEARCH_GAPS = """
Based on the limitations and conclusions from these studies, identify research gaps:

{limitations}

Provide:
1. **Acknowledged Gaps**: Limitations multiple papers recognize
2. **Unexplored Areas**: Questions not yet addressed
3. **Methodological Improvements**: How could future research be better?
4. **Suggested Directions**: What should researchers investigate next?

Research Gap Analysis:"""

# NEW: Citation Prompts

EXTRACT_CITATIONS = """
From the following reference section, extract and parse citations:

{reference_section}

For each citation, identify:
- Authors
- Year
- Title
- Journal/Source
- Volume/Pages (if available)

Format as a structured list."""

FORMAT_CITATION = """
Convert this citation information into {format} format:

Authors: {authors}
Year: {year}
Title: {title}
Journal: {journal}
Volume: {volume}
Pages: {pages}

Formatted Citation:"""

# -------------------------------
# QUERY CLASSIFICATION
# -------------------------------

CLASSIFY_QUERY = """
Classify the following user query into one of these categories:
- factual: Questions seeking specific facts or information
- creative: Requests for generating new content
- analytical: Requests for analysis or evaluation
- comparison: Requests to compare multiple items
- summarization: Requests to summarize content

Query: {query}

Classification (one word):"""

DETECT_DOMAIN = """
Identify the domain/field of this document:
- medical
- legal  
- technical/engineering
- scientific/research
- business
- general

Document excerpt:
{content}

Domain (one word):"""

# -------------------------------
# GENERIC UTILITY
# -------------------------------

def get_prompt_template(name: str) -> str:
    """
    Fetch a prompt template by name.
    """
    templates: Dict[str, str] = {
        # Original templates
        "document_summary": DOCUMENT_SUMMARY_PROMPT,
        "document_analysis": DOCUMENT_ANALYSIS_PROMPT,
        "conversation": CONVERSATION_PROMPT,
        "follow_up": FOLLOW_UP_PROMPT,
        "research_insight": RESEARCH_INSIGHT_PROMPT,
        
        # NEW: Summarization templates
        "summary_short": SUMMARY_SHORT,
        "summary_detailed": SUMMARY_DETAILED,
        "summary_bullet": SUMMARY_BULLET,
        "summary_section": SUMMARY_SECTION,
        
        # NEW: Comparison templates
        "comparison_documents": COMPARISON_DOCUMENTS,
        "comparison_methodologies": COMPARISON_METHODOLOGIES,
        "identify_contradictions": IDENTIFY_CONTRADICTIONS,
        
        # NEW: Analysis templates
        "trend_analysis": TREND_ANALYSIS,
        "research_gaps": RESEARCH_GAPS,
        
        # NEW: Citation templates
        "extract_citations": EXTRACT_CITATIONS,
        "format_citation": FORMAT_CITATION,
        
        # NEW: Classification templates
        "classify_query": CLASSIFY_QUERY,
        "detect_domain": DETECT_DOMAIN,
    }

    if name not in templates:
        raise ValueError(f"Unknown prompt template: {name}")

    return templates[name]


def get_all_template_names() -> list:
    """
    Return list of all available template names.
    """
    return [
        # Document templates
        "document_summary",
        "document_analysis",
        "summary_short",
        "summary_detailed",
        "summary_bullet",
        "summary_section",
        
        # Conversation templates
        "conversation",
        "follow_up",
        
        # Comparison templates
        "comparison_documents",
        "comparison_methodologies",
        "identify_contradictions",
        
        # Analysis templates
        "research_insight",
        "trend_analysis",
        "research_gaps",
        
        # Citation templates
        "extract_citations",
        "format_citation",
        
        # Classification templates
        "classify_query",
        "detect_domain",
    ]   