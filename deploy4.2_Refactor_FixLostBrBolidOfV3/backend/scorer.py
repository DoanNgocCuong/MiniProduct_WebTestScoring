# backend/scorer.py

import asyncio
import json
import logging
from openai import AsyncOpenAI, APIError, RateLimitError
import functools
from circuitbreaker import circuit

logger = logging.getLogger(__name__)

class Scorer:
    def __init__(self, api_key):
        self.api_key = api_key

    @circuit(failure_threshold=5, recovery_timeout=60)
    @functools.lru_cache(maxsize=100)
    async def score_essay(self, question, checking_answer, user_answer):
        async with AsyncOpenAI(api_key=self.api_key) as client:
            prompt = f"""
You are an expert at scoring short essay questions.
You are provided with one QUESTION and one CHECKING ANSWER for that QUESTION.
After the USER enters the USER ANSWER, you will check the USER ANSWER against the CHECKING ANSWER.

Instructions:
- Grade based on 3 criteria: accuracy (0-5 points), completeness (0-3 points), clarity (0-2 points) (total 10 points).
- Output: JSON format, with no additional text before or after:
{{
    "accuracy": {{
        "score": <score>,
        "reason": "<reason in Vietnamese>"
    }},
    "completeness": {{
        "score": <score>,
        "reason": "<reason in Vietnamese>"
    }},
    "clarity": {{
        "score": <score>,
        "reason": "<reason in Vietnamese>"
    }}
}}
Ensure all keys and values are enclosed in double quotes, except for score values which should be integers.
Do not include any explanations or text outside of this JSON structure.
---
QUESTION:
{question}
CHECKING ANSWER:
{checking_answer}
"""

            try:
                async with asyncio.timeout(10):
                    completion = await client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": prompt},
                            {"role": "user", "content": user_answer},
                        ],
                        temperature=0,
                        max_tokens=2048,
                    )
                logger.info("Received scoring from OpenAI")
                return json.loads(completion.choices[0].message.content)
            except (RateLimitError, APIError) as e:
                logger.error(f"OpenAI API error: {e}")
                raise
            except Exception as e:
                logger.error(f"Scoring error: {e}")
                raise
