TOPIC_CLASSIFIER_PROMPT = """
Classify the following aptitude question into a topic and problem type.

Available topics: {topics}
Available problem types per topic: {problem_types}

Question: {question_text}

Return JSON:
{{"topic": "topic_slug", "problem_type": "problem_type_slug", "confidence": 0.0-1.0}}
"""

SOLVER_STRATEGY_PROMPT = """
Given the following aptitude question, select the appropriate solving strategy.

Question: {question_text}
Topic: {topic}
Problem type: {problem_type}

Available strategies: {strategies}

Return JSON:
{{"strategy": "strategy_name", "variables": [], "formulas": [], "approach": "brief approach description"}}
"""

EXPLANATION_PROMPT = """
Generate a step-by-step explanation for the solved question.

Question: {question_text}
Solution steps: {solution_steps}

Return JSON:
{{"concept": "concept explanation", "approach": "how to approach similar questions", "steps": [{{"step": 1, "title": "...", "description": "..."}}]}}
"""

SIMILAR_QUESTION_PROMPT = """
Generate a similar practice question with different numerical values.

Original question: {question_text}
Topic: {topic}
Problem type: {problem_type}
Difficulty: {difficulty}

Return JSON:
{{"question_text": "...", "options": [], "correct_answer": "...", "explanation_concept": "...", "hints": []}}
"""

SOLVER_PROMPT = """
You are an aptitude question solver. Solve the following question step by step.

Question: {question_text}

Available topics: {topics}
Available problem types: {problem_types}

Return JSON with these exact fields:
{{
  "question_understanding": "brief restatement of the question",
  "topic": "matching topic slug or empty string if unknown",
  "problem_type": "matching problem type name or empty string if unknown",
  "concept": "the concept being tested",
  "approach": "how to approach and solve this question",
  "steps": [
    {{"step": 1, "title": "...", "calculation": "...", "explanation": "..."}}
  ],
  "final_answer": "the final answer only",
  "shortcut": "shortcut method if applicable, otherwise empty string",
  "confidence": 0.0-1.0
}}

Rules:
- Do not invent formulas. Use only standard aptitude methods.
- If unsure about topic or problem type, return empty strings.
- Never claim the answer is mathematically verified unless a verification system has confirmed it.
- Keep calculations simple and clear.
- final_answer should be concise.
- shortcut should be empty string if no useful shortcut exists.
"""

PRACTICE_QUESTION_PROMPT = """
Generate a similar practice aptitude question with different numerical values.

Original question: {question_text}
Topic: {topic}
Problem type: {problem_type}
Difficulty: {difficulty}
Concept: {concept}

Return JSON with these exact fields:
{{
  "question_text": "the complete practice question",
  "topic": "matching topic slug",
  "problem_type": "matching problem type name",
  "difficulty": "same difficulty as original",
  "concept": "the concept being tested",
  "approach": "how to approach and solve this question",
  "steps": [
    {{"step": 1, "title": "...", "calculation": "...", "explanation": "..."}}
  ],
  "final_answer": "the final answer only",
  "shortcut": "shortcut method if applicable, otherwise empty string",
  "confidence": 0.0-1.0
}}

Rules:
- Keep the same topic, problem type, difficulty, and concept as the original.
- Use different numerical values from the original.
- The question must be solvable using the same approach as the original.
- Do not invent formulas. Use only standard aptitude methods.
- final_answer should be concise.
- shortcut should be empty string if no useful shortcut exists.
"""
