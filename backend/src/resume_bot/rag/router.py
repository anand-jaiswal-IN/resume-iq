"""
Semantic Query Intent Router.
Classifies incoming user messages into:
  - GENERAL_CONVERSATION (greetings, meta-questions like 'can you evaluate a JD?', 'what can you do?')
  - JD_EVALUATION (pasting a job description or asking for fit rating/match against a role)
  - RESUME_SUMMARY (asking for a complete profile overview, elevator pitch, or summary)
  - FACTUAL_QA (asking specific questions about the resume content)
"""

from langchain_core.prompts import ChatPromptTemplate
from resume_bot.rag.chain import get_llm
from resume_bot.rag.models import QueryIntent


ROUTER_SYSTEM = """You are an intelligent query classifier for an AI Resume Bot pair-programmer and recruiter assistant.
Analyze the user's message and determine their primary intent:

1. 'GENERAL_CONVERSATION':
   - Greetings ('hello', 'hi', 'hey')
   - Inquiries about bot capabilities ('Can you evaluate a JD?', 'I have the JDs, I will provide to you. Could you give the rating that this candidate will be fit for this job or not?', 'What features do you have?')
   - Small talk or general questions not asking for specific facts inside the resume.

2. 'JD_EVALUATION':
   - The user has provided job description text, job requirements, or a role specification to evaluate candidate fit.
   - Or the user says e.g. 'Match candidate against this: [requirements]', 'Evaluate fit for Senior Python Developer...'.
   - Extract the entire job description text into `extracted_jd`.

3. 'RESUME_SUMMARY':
   - High-level overview requests: 'Summarize the candidate', 'Give me an elevator pitch', 'Overview of their background'.

4. 'FACTUAL_QA':
   - The user is asking a specific factual question about the candidate's skills, work experience, projects, education, contact info, or links.

Classify accurately and concisely.
"""

ROUTER_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", ROUTER_SYSTEM),
        ("human", "User message: {query}"),
    ]
)


def classify_intent(query: str) -> QueryIntent:
    """
    Classify the user's message into one of 4 pipeline paths.
    """
    # Fast heuristic checks for obvious greetings
    stripped = query.strip().lower()
    if stripped in ("hi", "hello", "hey", "help", "who are you", "what can you do"):
        return QueryIntent(
            intent="GENERAL_CONVERSATION",
            explanation="Standard greeting or capability inquiry.",
        )

    # Fast heuristic for direct JD keywords with long text
    if any(keyword in stripped for keyword in ("job description", "requirements:", "responsibilities:", "we are looking for", "key skills:")) and len(query) > 150:
        return QueryIntent(
            intent="JD_EVALUATION",
            explanation="User pasted job description text.",
            extracted_jd=query,
        )

    llm = get_llm()
    structured_llm = llm.with_structured_output(QueryIntent)

    router_chain = ROUTER_PROMPT | structured_llm
    try:
        result: QueryIntent = router_chain.invoke({"query": query})
        return result
    except Exception:
        # Fallback to FACTUAL_QA if classification fails
        return QueryIntent(
            intent="FACTUAL_QA",
            explanation="Defaulted to factual QA pipeline.",
        )
