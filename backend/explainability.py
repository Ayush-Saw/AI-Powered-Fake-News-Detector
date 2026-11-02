def explain(model, vectorizer, matrix, limit=8):
    try:
        estimator = model
        if hasattr(model, "named_steps"):
            estimator = list(model.named_steps.values())[-1]
        coef = estimator.coef_[0]
        names = vectorizer.get_feature_names_out()
        row = matrix.tocsr()
        scored = [(str(names[i]), float(v * coef[i])) for i, v in zip(row.indices, row.data) if i < len(coef)]
        scored.sort(key=lambda x: abs(x[1]), reverse=True)
        if not scored:
            return "No recognizable features were found."
        return "; ".join(f"{token} (contribution {score:.3f})" for token, score in scored[:limit])
    except Exception:
        return "Feature-level explanation is unavailable for this model type."
