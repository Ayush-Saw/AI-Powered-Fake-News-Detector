from sklearn.metrics.pairwise import cosine_similarity
from .prediction import load_artifacts, clean_text
from .database import list_analyses

def find_similar(text, limit=8):
    _, vectorizer = load_artifacts()
    if vectorizer is None: return []
    q = vectorizer.transform([clean_text(text)])
    found=[]
    for row in list_analyses(500):
        candidate=vectorizer.transform([clean_text(row["title"]+" "+row["article_text"])])
        score=float(cosine_similarity(q,candidate)[0][0])*100
        if score >= 1:
            found.append({"id":row["id"],"title":row["title"],"prediction":row["prediction"],
                          "created_at":row["created_at"],"similarity":round(score,2)})
    return sorted(found,key=lambda x:x["similarity"],reverse=True)[:limit]
