def check_transparency(promised,actual):
    issues=[]
    for category , amount in promised.items():
        if category  not in actual or actual[category]<amount*0.8:
            issues.append(f"mismatch in {category}: promised {amount}, spent {actual.get(category,0)}")
    return issues if issues else ["transparent"]