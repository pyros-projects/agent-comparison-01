"""LLM service using litellm for analysis."""
import json
from typing import List, Optional
import litellm
from litellm import completion, embedding

from .config import settings


class LLMService:
    """Service for LLM interactions."""
    
    def __init__(self):
        """Initialize the LLM service."""
        litellm.set_verbose = False
    
    def analyze_paper(self, title: str, abstract: str, content: Optional[str] = None) -> dict:
        """Analyze a paper and extract structured information."""
        content_text = content[:5000] if content else ""  # Limit content for context
        
        prompt = f"""Analyze the following research paper and provide a structured analysis in JSON format.

Title: {title}

Abstract: {abstract}

{('Content excerpt: ' + content_text) if content_text else ''}

Please provide a JSON response with the following structure:
{{
    "summary": "A concise summary of the paper (2-3 sentences)",
    "tags": ["tag1", "tag2", "tag3", ...],
    "questions_answered": ["Question 1", "Question 2", ...],
    "key_findings": ["Finding 1", "Finding 2", ...],
    "relevancy_score": <number between 0 and 10>,
    "interesting_score": <number between 0 and 10>
}}

Focus on AI/ML related papers. Tags should be specific and relevant. Questions should be what problems or questions this paper addresses. Key findings should be the main contributions or discoveries.
"""
        
        try:
            response = completion(
                model=settings.default_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            # Ensure scores are floats and within range
            result['relevancy_score'] = max(0, min(10, float(result.get('relevancy_score', 5))))
            result['interesting_score'] = max(0, min(10, float(result.get('interesting_score', 5))))
            
            return result
        except Exception as e:
            print(f"Error analyzing paper: {e}")
            # Return default values on error
            return {
                "summary": f"Analysis of {title}",
                "tags": ["ai", "research"],
                "questions_answered": [],
                "key_findings": [],
                "relevancy_score": 5.0,
                "interesting_score": 5.0
            }
    
    def analyze_repository(self, name: str, description: str, readme: Optional[str] = None) -> dict:
        """Analyze a repository and extract structured information."""
        readme_text = readme[:5000] if readme else ""  # Limit readme for context
        
        prompt = f"""Analyze the following GitHub repository and provide a structured analysis in JSON format.

Name: {name}

Description: {description}

{('README excerpt: ' + readme_text) if readme_text else ''}

Please provide a JSON response with the following structure:
{{
    "summary": "A concise summary of the repository (2-3 sentences)",
    "tags": ["tag1", "tag2", "tag3", ...],
    "questions_answered": ["Question 1", "Question 2", ...],
    "key_findings": ["Finding 1", "Finding 2", ...],
    "relevancy_score": <number between 0 and 10>,
    "interesting_score": <number between 0 and 10>
}}

Focus on AI/ML related repositories. Tags should be specific and relevant. Questions should be what problems or questions this repository addresses. Key findings should be the main features or capabilities.
"""
        
        try:
            response = completion(
                model=settings.default_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            # Ensure scores are floats and within range
            result['relevancy_score'] = max(0, min(10, float(result.get('relevancy_score', 5))))
            result['interesting_score'] = max(0, min(10, float(result.get('interesting_score', 5))))
            
            return result
        except Exception as e:
            print(f"Error analyzing repository: {e}")
            # Return default values on error
            return {
                "summary": f"Analysis of {name}",
                "tags": ["ai", "code"],
                "questions_answered": [],
                "key_findings": [],
                "relevancy_score": 5.0,
                "interesting_score": 5.0
            }
    
    def analyze_theory(self, theory: str, papers: List[dict], repos: List[dict]) -> dict:
        """Analyze a theory against papers and repositories."""
        papers_text = "\n".join([f"- {p.get('title', 'Unknown')}: {p.get('summary', '')}" for p in papers[:10]])
        repos_text = "\n".join([f"- {r.get('name', 'Unknown')}: {r.get('summary', '')}" for r in repos[:10]])
        
        prompt = f"""Given the following theory or question:

"{theory}"

And the following related papers and repositories:

Papers:
{papers_text}

Repositories:
{repos_text}

Please analyze and provide a JSON response with:
{{
    "supporting_count": <number of items that support the theory>,
    "opposing_count": <number of items that oppose the theory>,
    "related_theories": ["Related theory 1", "Related theory 2", ...],
    "suggestions": ["Suggestion 1", "Suggestion 2", ...]
}}

Suggestions should include related questions or theories to explore, or recommendations to gather more data.
"""
        
        try:
            response = completion(
                model=settings.default_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            return json.loads(result_text)
        except Exception as e:
            print(f"Error analyzing theory: {e}")
            return {
                "supporting_count": 0,
                "opposing_count": 0,
                "related_theories": [],
                "suggestions": ["Consider starting cataloguing mode to gather more data"]
            }
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text."""
        try:
            response = embedding(
                model=settings.default_embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return []


llm_service = LLMService()

