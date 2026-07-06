import json
import re
import os
import requests
from bs4 import BeautifulSoup
from difflib import SequenceMatcher

def clean_text(text):
    """Normalize whitespace and strip non-alphanumeric characters for clean comparison."""
    if not isinstance(text, str):
        text = str(text)
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

# Mappings of schema types to text-extraction functions
def extract_faq_texts(node):
    texts = []
    questions = node.get("mainEntity", [])
    if not isinstance(questions, list):
        questions = [questions]
    for faq in questions:
        if not isinstance(faq, dict):
            continue
        q_text = faq.get("name", "")
        ans_data = faq.get("acceptedAnswer", {})
        ans_text = ans_data.get("text", "") if isinstance(ans_data, dict) else ""
        if q_text:
            texts.append(("Question", q_text))
        if ans_text:
            # Strip HTML tags from answer text
            clean_ans = BeautifulSoup(ans_text, "html.parser").get_text()
            texts.append(("Answer", clean_ans))
    return texts

def extract_recipe_texts(node):
    texts = []
    if node.get("name"):
        texts.append(("Recipe Name", node["name"]))
    
    ingredients = node.get("recipeIngredient", [])
    if isinstance(ingredients, list):
        for ing in ingredients:
            if isinstance(ing, str):
                texts.append(("Ingredient", ing))
    elif isinstance(ingredients, str):
        texts.append(("Ingredient", ingredients))
        
    instructions = node.get("recipeInstructions", [])
    if isinstance(instructions, list):
        for step in instructions:
            if isinstance(step, dict):
                texts.append(("Instruction Step", step.get("text", "")))
            elif isinstance(step, str):
                texts.append(("Instruction Step", step))
    elif isinstance(instructions, str):
        texts.append(("Instruction Step", instructions))
    return texts

def extract_breadcrumb_texts(node):
    texts = []
    items = node.get("itemListElement", [])
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                name = ""
                item_val = item.get("item")
                if isinstance(item_val, dict):
                    name = item_val.get("name") or item.get("name", "")
                else:
                    name = item.get("name", "")
                if name:
                    texts.append(("Breadcrumb Name", name))
    return texts

def extract_review_texts(node):
    texts = []
    if node.get("reviewBody"):
        texts.append(("Review Body", node["reviewBody"]))
    
    author = node.get("author", {})
    if isinstance(author, dict) and author.get("name"):
        texts.append(("Reviewer Name", author["name"]))
    elif isinstance(author, str):
        texts.append(("Reviewer Name", author))
    return texts

def extract_product_texts(node):
    texts = []
    if node.get("name"):
        texts.append(("Product Name", node["name"]))
    if node.get("description"):
        texts.append(("Product Description", node["description"]))
    return texts

def extract_job_texts(node):
    texts = []
    if node.get("title"):
        texts.append(("Job Title", node["title"]))
    if node.get("description"):
        texts.append(("Job Description", node["description"]))
    return texts

SCHEMA_FIELD_MAPPINGS = {
    "FAQPage": extract_faq_texts,
    "Recipe": extract_recipe_texts,
    "BreadcrumbList": extract_breadcrumb_texts,
    "Review": extract_review_texts,
    "Product": extract_product_texts,
    "JobPosting": extract_job_texts
}

def audit_url(url, similarity_threshold=0.80):
    """Audits target URL for hidden schema structured data spam across multiple schema types."""
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
    parsed_schemas = []
    
    for script in json_ld_scripts:
        try:
            data = json.loads(script.get_text() or "")
            
            # Recursive function to gather all dict nodes (handling lists and @graph blocks)
            def gather_nodes(item):
                nodes = []
                if isinstance(item, list):
                    for sub in item:
                        nodes.extend(gather_nodes(sub))
                elif isinstance(item, dict):
                    if "@graph" in item:
                        nodes.extend(gather_nodes(item["@graph"]))
                    else:
                        nodes.append(item)
                return nodes
                
            all_nodes = gather_nodes(data)
            
            for node in all_nodes:
                t = node.get("@type")
                if isinstance(t, list):
                    for single_t in t:
                        if single_t in SCHEMA_FIELD_MAPPINGS:
                            parsed_schemas.append((single_t, node))
                elif isinstance(t, str) and t in SCHEMA_FIELD_MAPPINGS:
                    parsed_schemas.append((t, node))
        except Exception:
            continue
            
    if not parsed_schemas:
        return {"status": "PASS", "message": "No auditable structured data (FAQ, Recipe, Breadcrumb, Review, Product, JobPosting) found."}
        
    violations = []
    total_fields = 0
    passed_fields = 0
    
    for schema_type, schema in parsed_schemas:
        extractor = SCHEMA_FIELD_MAPPINGS[schema_type]
        fields_to_check = extractor(schema)
        
        for field_label, field_text in fields_to_check:
            if not field_text:
                continue
            total_fields += 1
            score = check_similarity(field_text, visible_text)
            
            if score < similarity_threshold:
                violations.append({
                    "schema_type": schema_type,
                    "field": field_label,
                    "expected_text": field_text[:100] + "..." if len(field_text) > 100 else field_text,
                    "similarity_score": score,
                    "status": "VIOLATION_HIDDEN"
                })
            else:
                passed_fields += 1
                
    compliance_score = round((passed_fields / total_fields) * 100, 1) if total_fields > 0 else 100.0
    return {
        "status": "WARNING" if violations else "PASS",
        "url": url,
        "total_fields_audited": total_fields,
        "failed_fields_count": len(violations),
        "compliance_score": f"{compliance_score}%",
        "violations": violations
    }
