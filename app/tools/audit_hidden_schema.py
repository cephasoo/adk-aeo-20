import json
import re
import os
import requests
from bs4 import BeautifulSoup
from difflib import SequenceMatcher

def clean_text(text):
    """Normalize whitespace and strip non-alphanumeric characters for clean comparison."""
    text = re.sub(r'\s+', ' ', text.lower())
    return re.sub(r'[^a-z0-9 ]', '', text).strip()

def get_visible_text(soup):
    """Extract and combine all human-readable text from the HTML body, excluding code and nav."""
    import copy
    temp_soup = copy.copy(soup)
    for element in temp_soup(["script", "style", "header", "footer", "nav", "iframe", "noscript"]):
        element.decompose()
    # Use separator=' ' to prevent block elements from merging into run-on words
    return clean_text(temp_soup.get_text(separator=' '))

def check_similarity(substring, visible_text):
    """Check if the FAQ substring exists or has a high similarity match within the page text."""
    clean_sub = clean_text(substring)
    if not clean_sub:
        return 1.0
    if clean_sub in visible_text:
        return 1.0
    
    # Fuzzy match logic using windowed sequence comparisons
    sub_words = clean_sub.split()
    sub_len = len(sub_words)
    page_words = visible_text.split()
    
    if len(page_words) < sub_len:
        return 0.0
    max_ratio = 0.0
    # Slide a window across the visible text to find the best match candidate
    for i in range(len(page_words) - sub_len + 1):
        window = " ".join(page_words[i : i + sub_len])
        ratio = SequenceMatcher(None, clean_sub, window).ratio()
        if ratio > max_ratio:
            max_ratio = ratio
        if max_ratio > 0.95:  # Fast break
            return 1.0
            
    return round(max_ratio, 2)

def audit_url(url, similarity_threshold=0.80):
    """Audits target URL for hidden FAQ schema spam."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        return {"error": f"Failed to retrieve URL: {str(e)}", "status": "FAIL"}
    
    soup = BeautifulSoup(response.content, "html.parser")
    visible_text = get_visible_text(soup)
    
    # Extract JSON-LD blocks
    json_ld_scripts = soup.find_all("script", type="application/ld+json")
    faq_schemas = []
    
    for script in json_ld_scripts:
        try:
            data = json.loads(script.get_text() or "")
            # Handle both single objects and nested graphs
            nodes = data.get("@graph", [data]) if isinstance(data, dict) else [data]
            for node in nodes:
                if isinstance(node, dict) and node.get("@type") == "FAQPage":
                    faq_schemas.append(node)
        except Exception:
            continue
            
    if not faq_schemas:
        return {"status": "PASS", "message": "No FAQPage structured data found on this page."}
        
    violations = []
    total_faqs = 0
    passed_faqs = 0
    
    for schema in faq_schemas:
        questions = schema.get("mainEntity", [])
        if not isinstance(questions, list):
            questions = [questions]
        for faq in questions:
            total_faqs += 1
            question_text = faq.get("name", "")
            answer_data = faq.get("acceptedAnswer", {})
            answer_text = answer_data.get("text", "") if isinstance(answer_data, dict) else ""
            
            # Clean HTML out of schema answer text
            answer_text = BeautifulSoup(answer_text, "html.parser").get_text()
            q_score = check_similarity(question_text, visible_text)
            a_score = check_similarity(answer_text, visible_text)
            
            if q_score < similarity_threshold or a_score < similarity_threshold:
                violations.append({
                    "question": question_text,
                    "question_similarity": q_score,
                    "answer_snippet": answer_text[:100] + "...",
                    "answer_similarity": a_score,
                    "status": "VIOLATION_HIDDEN"
                })
            else:
                passed_faqs += 1
                
    compliance_score = round((passed_faqs / total_faqs) * 100, 1) if total_faqs > 0 else 100.0
    return {
        "status": "WARNING" if violations else "PASS",
        "url": url,
        "total_faqs_in_schema": total_faqs,
        "failed_faqs_in_schema": len(violations),
        "compliance_score": f"{compliance_score}%",
        "violations": violations
    }
