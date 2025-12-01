# RAG (Question Answering) Prompt

## Prompt Template

```
Answer the following question based ONLY on the provided contract documents.
Include specific references to document sections when possible.

QUESTION: {user_question}

DOCUMENTS:
{context}

Provide a clear, accurate answer with citations. If the answer is not in the documents, say so.

ANSWER:
```

## Rationale

**Why this prompt structure:**

1. **Grounding Instruction**: "based ONLY on" prevents hallucination from model's training data
2. **Citation Request**: Encourages model to reference specific sections
3. **Honesty Clause**: "If not in documents, say so" reduces false positives

**Design Decisions:**

- **Temperature**: 0.3 (balanced - some creativity for natural answers, but grounded)
- **Max Tokens**: 1000 (sufficient for detailed answers)
- **Context Window**: 5000 chars per document (balance between cost and coverage)

**Prompt Engineering Techniques Used:**

1. **Role Specification**: Implicit - treating as Q&A expert
2. **Format Guidance**: "Clear, accurate answer" sets expectation
3. **Negative Examples**: "If answer not in documents" handles edge case

**Why Not Chain-of-Thought:**

Chain-of-thought ("Let's think step by step") was tested but:
- Increased response time by 2-3 seconds
- Didn't improve accuracy for factual extraction
- Made citation extraction harder (more parsing needed)

**Citation Extraction:**

Post-processing uses regex to find document references:
- Pattern: `[DOCUMENT: doc_id]` markers in context
- Fallback: Filename mentions in answer
- Page numbers: Extracted from `[PAGE N]` markers

**Alternative Approaches Tested:**

1. **Separate citation prompt**: Two-stage (answer → citations) - too slow
2. **Structured JSON output**: Model forced citations but reduced answer quality
3. **Current approach**: Natural language + post-processing - best balance