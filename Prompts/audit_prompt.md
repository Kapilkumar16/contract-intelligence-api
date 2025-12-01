# Audit (Risk Detection) Prompt

## Prompt Template

```
You are a legal contract auditor. Analyze this contract for risky clauses.

RISK CATEGORIES TO CHECK:
1. Auto-renewal with less than 30 days notice
2. Unlimited liability or no liability cap
3. Broad indemnity clauses
4. One-sided termination rights
5. Unfavorable payment terms
6. Lack of confidentiality protections
7. Unclear dispute resolution

For each risk found, return a JSON array with this structure:
[
  {
    "severity": "high|medium|low",
    "clause_type": "auto_renewal|liability|indemnity|termination|payment|confidentiality|other",
    "description": "Brief description of the risk",
    "evidence": "Exact quote from contract (keep it short)",
    "recommendation": "How to mitigate this risk"
  }
]

CONTRACT TEXT:
{document_text}

Return ONLY the JSON array, no other text.

JSON OUTPUT:
```

## Rationale

**Why this prompt structure:**

1. **Expert Role**: "Legal contract auditor" activates specialized knowledge
2. **Explicit Risk Categories**: Guides model to check specific, actionable items
3. **Severity Classification**: Forces prioritization (high/medium/low)
4. **Evidence Requirement**: Grounds findings in actual text (reduces false positives)

**Design Decisions:**

- **Temperature**: 0.1 (very low - want consistent, conservative risk assessment)
- **Max Tokens**: 2000 (allows multiple findings)
- **Structured Output**: JSON array for easy parsing and display

**Risk Category Selection:**

Chosen based on common contract pitfalls:
- **Auto-renewal**: Catches surprise renewals (user pain point)
- **Liability**: Financial risk assessment (high-value)
- **Indemnity**: Legal risk (often overlooked)
- **Termination**: Exit strategy (negotiation point)
- **Payment**: Cash flow impact (business critical)
- **Confidentiality**: IP protection (common in NDAs)
- **Dispute**: Conflict resolution (cost saver)

**Severity Calibration:**

```
HIGH: Financial risk >$100K or legal exposure
MEDIUM: Negotiable unfavorable terms
LOW: Minor issues or missing standard clauses
```

**Why Evidence is Critical:**

- Prevents hallucinated risks
- Allows user to verify finding
- Enables legal review
- Builds trust in system

**Alternative Approaches Considered:**

1. **Rule-based only**: Too rigid, misses context
2. **Separate prompts per risk**: 7x API calls - too slow
3. **Current (unified)**: One call, comprehensive - optimal

**Post-Processing:**

If JSON parsing fails:
- Return single low-severity finding
- Log error for monitoring
- Ensures system never crashes on bad output