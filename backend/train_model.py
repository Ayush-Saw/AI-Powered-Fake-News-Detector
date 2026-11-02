import json
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from .config import DATASET, MODEL_DIR, MODEL_PATH, VECTORIZER_PATH, INFO_PATH

def label_clean(x):
    x=str(x).strip().lower()
    if x in {"fake","false","0","untrue"}: return "fake"
    if x in {"real","true","1","reliable"}: return "real"
    return None

def main():
    if not DATASET.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET}. Copy your existing fake_news.csv there.")
    df=pd.read_csv(DATASET); df.columns=[str(c).strip().lower() for c in df.columns]
    if "label" not in df: raise ValueError("CSV needs a 'label' column.")
    cols=[c for c in ("title","text") if c in df]
    if not cols: raise ValueError("CSV needs 'title' and/or 'text'.")
    df["target"]=df["label"].map(label_clean)
    df=df.dropna(subset=["target"]).copy()
    df["combined"]=df[cols].fillna("").astype(str).agg(" ".join,axis=1).str.replace(r"\s+"," ",regex=True).str.strip()
    df=df[df["combined"].str.len()>0].drop_duplicates(subset=["combined","target"])
    if df["target"].nunique()!=2: raise ValueError("Both fake and real labels are required.")
    X_train,X_test,y_train,y_test=train_test_split(df["combined"],df["target"],test_size=.2,random_state=42,stratify=df["target"])
    vec=TfidfVectorizer(max_features=50000,ngram_range=(1,2),min_df=2,sublinear_tf=True)
    xtr=vec.fit_transform(X_train); xte=vec.transform(X_test)
    model=LinearSVC(); model.fit(xtr,y_train); pred=model.predict(xte)
    info={"accuracy":round(float(accuracy_score(y_test,pred)),6),
          "macro_precision":round(float(precision_score(y_test,pred,average="macro",zero_division=0)),6),
          "macro_recall":round(float(recall_score(y_test,pred,average="macro",zero_division=0)),6),
          "macro_f1":round(float(f1_score(y_test,pred,average="macro",zero_division=0)),6),
          "test_records":int(len(y_test)),"split_method":"80/20 stratified train/test split, random_state=42",
          "dataset_records_after_cleaning":int(len(df)),"label_counts":{str(k):int(v) for k,v in df["target"].value_counts().to_dict().items()},
          "model":"TF-IDF (1-2 grams, max_features=50000) + LinearSVC",
          "note":"Metrics computed on this run's held-out split. Dataset leakage and source artifacts may inflate results."}
    MODEL_DIR.mkdir(parents=True,exist_ok=True)
    joblib.dump(model,MODEL_PATH); joblib.dump(vec,VECTORIZER_PATH)
    INFO_PATH.write_text(json.dumps(info,indent=2),encoding="utf-8")
    print("\nACTUAL HELD-OUT METRICS FOR THIS RUN\n"+json.dumps(info,indent=2))
    print(classification_report(y_test,pred,zero_division=0))
if __name__=="__main__": main()
