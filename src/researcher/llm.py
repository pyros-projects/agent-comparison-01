import os
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import litellm
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

# Configure LiteLLM for Azure
# The .env provides AZURE_API_KEY, AZURE_API_BASE, AZURE_API_VERSION
# litellm automatically uses these if they are in os.environ and match expected names
# or we can pass them explicitly.

class LLMClient:
    def __init__(self):
        self.model = os.getenv("DEFAULT_MODEL", "azure/gpt-4.1")
        self.embedding_model = os.getenv("DEFAULT_EMBEDDING_MODEL", "azure/text-embedding-3-small")
        # Ensure API base ends with / if needed, or matches what litellm expects
        # For Azure, litellm usually expects AZURE_API_BASE to be the resource endpoint.

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_embedding(self, text: str) -> List[float]:
        if not text: return []
        try:
            response = litellm.embedding(
                model=self.embedding_model,
                input=[text]
            )
            return response['data'][0]['embedding']
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _call_llm(self, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        response = litellm.completion(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"} if json_mode else None
        )
        return response.choices[0].message.content

    def analyze_paper(self, text: str) -> Dict[str, Any]:
        prompt = """
        You are an expert research assistant. Analyze the following research paper content (or summary).
        Extract the following information in JSON format:
        - summary: A concise summary of the paper.
        - tags: List of relevant tags/keywords.
        - questions_answered: List of questions this paper answers.
        - key_findings: List of key findings.
        - relevancy_score: A score from 0 to 10 indicating real-world relevancy.
        - interesting_score: A score from 0 to 10 indicating how interesting/novel it is.
        
        Content:
        {text}
        """
        messages = [
            {"role": "system", "content": "You are a helpful research assistant that outputs JSON."},
            {"role": "user", "content": prompt.format(text=text[:15000])} # Truncate to avoid context limits if necessary
        ]
        
        try:
            response = self._call_llm(messages, json_mode=True)
            return json.loads(response)
        except Exception as e:
            print(f"Error analyzing paper: {e}")
            return {
                "summary": "Error analyzing paper",
                "tags": [],
                "questions_answered": [],
                "key_findings": [],
                "relevancy_score": 0,
                "interesting_score": 0
            }

    def analyze_repository(self, readme_text: str, file_structure: str) -> Dict[str, Any]:
        prompt = """
        You are an expert software researcher. Analyze the following repository README and file structure.
        Extract the following information in JSON format:
        - summary: A concise summary of the repository purpose and features.
        - tags: List of relevant tags/technologies.
        - questions_answered: List of questions this repository answers (e.g., "How to implement X?").
        - key_findings: List of key features or architectural findings.
        - relevancy_score: A score from 0 to 10.
        - interesting_score: A score from 0 to 10.

        README:
        {readme}

        File Structure:
        {structure}
        """
        messages = [
            {"role": "system", "content": "You are a helpful research assistant that outputs JSON."},
            {"role": "user", "content": prompt.format(
                readme=readme_text[:10000], 
                structure=file_structure[:5000]
            )}
        ]
        
        try:
            response = self._call_llm(messages, json_mode=True)
            return json.loads(response)
        except Exception as e:
            print(f"Error analyzing repository: {e}")
            return {
                "summary": "Error analyzing repository",
                "tags": [],
                "questions_answered": [],
                "key_findings": [],
                "relevancy_score": 0,
                "interesting_score": 0
            }

    def find_relationships(self, item1: Dict, item2: Dict) -> Optional[Dict[str, Any]]:
        # Returns a relationship object if related, else None
        prompt = """
        Analyze the relationship between these two research items.
        
        Item 1: {title1} - {summary1}
        Item 2: {title2} - {summary2}
        
        Are they related? If yes, describe the relationship.
        Return JSON:
        {{
            "is_related": boolean,
            "type": "string (e.g. 'related', 'sub-topic', 'conflicts', 'extends')",
            "description": "short description",
            "weight": float (0.0 to 1.0)
        }}
        """
        messages = [
            {"role": "system", "content": "You are a helpful research assistant that outputs JSON."},
            {"role": "user", "content": prompt.format(
                title1=item1.get('title'), summary1=item1.get('summary'),
                title2=item2.get('title'), summary2=item2.get('summary')
            )}
        ]
        
        try:
            response = self._call_llm(messages, json_mode=True)
            return json.loads(response)
        except Exception:
            return None

    def answer_theory(self, theory: str, context_items: List[Dict]) -> str:
        context_str = "\n\n".join([
            f"Title: {item['title']}\nSummary: {item['summary']}\nFindings: {item['key_findings']}"
            for item in context_items
        ])
        prompt = """
        The user has a theory or question: "{theory}"
        
        Based on the following research items, analyze if the theory is supported or what the consensus is.
        
        Context:
        {context}
        
        Provide a detailed answer referencing the items.
        """
        messages = [
            {"role": "system", "content": "You are a helpful research assistant."},
            {"role": "user", "content": prompt.format(theory=theory, context=context_str)}
        ]
        return self._call_llm(messages)
