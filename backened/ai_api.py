def ai_reasoning(receipt_text):
    suspicious_terms=["miscellaneous","consultancy","urgent_fee"]
    for term in suspicious_terms:
        if term in receipt_text.lower():
            return {"explanation":f"Suspicious term detected: {term}"}
    return {"explanation":"No suspicious terms detected"}