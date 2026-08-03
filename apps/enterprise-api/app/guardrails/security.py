import re
from typing import Dict, Any, Tuple, List

# Common prompt injection & jailbreak keywords / patterns
INJECTION_PATTERNS = [
    r"ignore (?:all )?previous instructions",
    r"ignore all instructions",
    r"disregard system prompt",
    r"you are now in DAN mode",
    r"do anything now",
    r"override security protocols",
    r"act as an unfiltered AI",
    r"bypass safety rules"
]

# PII Regex Patterns
PII_PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b(?:\d[ -]*?){13,16}\b"
}

def detect_prompt_injection(user_input: str) -> Tuple[bool, str]:
    """Check for prompt injection and jailbreak patterns."""
    lowered = user_input.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            return True, f"Security Warning: Potential prompt injection detected matching pattern '{pattern}'."
    return False, ""

def mask_pii(text: str) -> str:
    """Mask PII fields (email, phone, SSN, credit cards) in text."""
    masked_text = text
    masked_text = re.sub(PII_PATTERNS["email"], "[MASKED_EMAIL]", masked_text)
    masked_text = re.sub(PII_PATTERNS["phone"], "[MASKED_PHONE]", masked_text)
    masked_text = re.sub(PII_PATTERNS["ssn"], "[MASKED_SSN]", masked_text)
    masked_text = re.sub(PII_PATTERNS["credit_card"], "[MASKED_CARD]", masked_text)
    return masked_text

def validate_input(user_input: str) -> Tuple[bool, str, str]:
    """
    Validate and sanitize input query.
    Returns: (is_valid, sanitized_text, error_reason)
    """
    if not user_input or not user_input.strip():
        return False, "", "Empty prompt input."
    
    if len(user_input) > 8000:
        return False, "", "Prompt exceeds maximum allowed length of 8000 characters."
    
    is_injection, reason = detect_prompt_injection(user_input)
    if is_injection:
        return False, user_input, reason
        
    sanitized = mask_pii(user_input)
    return True, sanitized, ""

def calculate_dynamic_confidence(
    retrieved_chunks: List[Dict[str, Any]],
    response_text: str,
    context_text: str,
    zero_chunks: bool = False
) -> Tuple[bool, float]:
    """
    Calculate dynamic confidence score based on:
    1. Retrieval Chunk Scores
    2. Chunk Count & Density
    3. Faithfulness & Context Word Overlap
    Returns: (is_faithful, computed_confidence_score)
    """
    if zero_chunks or not retrieved_chunks or not context_text or not context_text.strip():
        return False, 0.0

    # 1. Retrieval Score Component (max 0.40)
    scores = [c.get("score", 0.5) for c in retrieved_chunks]
    avg_retrieval_score = sum(scores) / len(scores) if scores else 0.0
    retrieval_comp = min(0.40, avg_retrieval_score * 0.40)

    # 2. Context Word Overlap Component (max 0.45)
    context_words = set(re.findall(r"\w+", context_text.lower()))
    response_words = [w for w in re.findall(r"\w+", response_text.lower()) if len(w) > 3]
    
    if not response_words:
        overlap_comp = 0.20
    else:
        matched = sum(1 for w in response_words if w in context_words)
        ratio = matched / len(response_words)
        overlap_comp = round(ratio * 0.45, 2)

    # 3. Density / Chunk Count Component (max 0.15)
    density_comp = min(0.15, len(retrieved_chunks) * 0.04)

    # Total Score Calculation (bounded between 0.0 and 0.98)
    computed_score = round(max(0.10, min(0.98, retrieval_comp + overlap_comp + density_comp)), 2)
    is_faithful = computed_score >= 0.50

    return is_faithful, computed_score

def validate_output_against_context(response_text: str, context_text: str) -> Tuple[bool, float]:
    """Legacy wrapper delegating to dynamic confidence calculator."""
    return calculate_dynamic_confidence([], response_text, context_text, zero_chunks=False)
