import requests, re, html
def search_evidence(query, limit=6):
    if not (query or "").strip():
        return []
    try:
        r = requests.get("https://en.wikipedia.org/w/api.php", params={
            "action":"query","list":"search","srsearch":query[:300],"format":"json","srlimit":min(max(limit,1),10)
        }, headers={"User-Agent":"TruthLensStudentProject/1.0"}, timeout=8)
        r.raise_for_status()
        out=[]
        for x in r.json().get("query",{}).get("search",[]):
            title=x.get("title","")
            out.append({"title":title,"snippet":html.unescape(re.sub("<.*?>","",x.get("snippet",""))),
                        "url":"https://en.wikipedia.org/wiki/"+title.replace(" ","_")})
        return out
    except Exception:
        return []
