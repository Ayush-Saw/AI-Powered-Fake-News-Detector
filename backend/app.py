from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file, session
from .config import MAX_TEXT_CHARS
from .database import (init_db, save_analysis, get_analysis, list_analyses, delete_analysis, add_feedback,
                        create_user, get_user_by_email, get_user, list_users, list_user_analyses, dashboard_stats)
from functools import wraps
import os
from werkzeug.security import generate_password_hash, check_password_hash
from .prediction import predict_text, load_artifacts, model_info, clean_text
from .explainability import explain
from .evidence_search import search_evidence
from .duplicate_detection import find_similar
from .report_generator import create_report

app=Flask(__name__,template_folder="../templates",static_folder="../static")
app.secret_key=os.environ.get("TRUTHLENS_SECRET_KEY", "dev-only-change-this-secret-key")
init_db()

# A development admin is created on first run. Set ADMIN_EMAIL and ADMIN_PASSWORD
# before deployment; never expose the default credentials on a public server.
_admin_email=os.environ.get("ADMIN_EMAIL", "admin@truthlens.local")
_admin_password=os.environ.get("ADMIN_PASSWORD", "Admin@123")
if not get_user_by_email(_admin_email):
    create_user("Administrator", _admin_email, generate_password_hash(_admin_password), "admin")

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "error")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in as an administrator.", "error")
            return redirect(url_for("login", next=request.path))
        if session.get("role") != "admin":
            flash("Administrator access is required.", "error")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)
    return wrapped

@app.context_processor
def inject_current_user():
    user = get_user(session["user_id"]) if session.get("user_id") else None
    return {"current_user": user}

@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("dashboard" if session.get("role") == "user" else "admin_dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()[:80]
        email = request.form.get("email", "").strip().lower()[:180]
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name and email, and use a password of at least 8 characters.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif get_user_by_email(email):
            flash("An account with this email already exists.", "error")
        else:
            create_user(name, email, generate_password_hash(password), "user")
            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("user_id"):
        if session.get("role") == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = get_user_by_email(email)

        if (
            user
            and user["role"] == "admin"
            and check_password_hash(user["password_hash"], password)
        ):
            session.clear()
            session["user_id"] = user["id"]
            session["role"] = "admin"
            session["user_name"] = user["name"]

            flash("Admin login successful!", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin email or password.", "error")

    return render_template("admin_login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard" if session.get("role") == "user" else "admin_dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_user_by_email(email)
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["user_name"] = user["name"]
            flash("Welcome back!", "success")
            target = request.args.get("next", "")
            if target.startswith("/") and not target.startswith("//"):
                return redirect(target)
            return redirect(url_for("admin_dashboard" if user["role"] == "admin" else "dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")

@app.get("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.get("/dashboard")
@login_required
def dashboard():
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    rows = list_user_analyses(session["user_id"], 200)
    return render_template("dashboard.html", rows=rows,
        total=len(rows), fake=sum(r["prediction"] == "Likely Fake" for r in rows),
        real=sum(r["prediction"] == "Likely Real" for r in rows))

@app.get("/admin/dashboard")
@admin_required
def admin_dashboard():
    return render_template("admin_dashboard.html", stats=dashboard_stats(), users=list_users(100), rows=list_analyses(20))


def ready():
    m,v=load_artifacts()
    return m is not None and v is not None

@app.context_processor
def globals_for_templates(): return {"model_ready":ready()}

@app.get("/")
def home():
    return render_template("index.html",recent=list_analyses(5),info=model_info())

@app.route("/detect",methods=["GET","POST"])
def detect():
    if request.method=="GET": return render_template("detect.html")
    title=clean_text(request.form.get("title",""))[:300]
    text=clean_text(request.form.get("article_text",""))
    source=clean_text(request.form.get("source",""))[:300]
    combined=(title+" "+text).strip()
    if not combined:
        flash("Enter a headline or article first.","error"); return redirect(url_for("detect"))
    if len(combined)>MAX_TEXT_CHARS:
        flash(f"Keep text under {MAX_TEXT_CHARS:,} characters.","error"); return redirect(url_for("detect"))
    try: result=predict_text(combined)
    except Exception as e:
        flash(str(e),"error"); return redirect(url_for("detect"))
    m,v=load_artifacts()
    why=explain(m,v,result["matrix"])
    aid=save_analysis(title or combined[:100],text or combined,result["prediction"],result["confidence"],
                      result["language"],result["translated"],why,source,session.get("user_id"))
    return redirect(url_for("result",aid=aid,warning=result["warning"] or ""))

@app.get("/result/<int:aid>")
def result(aid):
    item=get_analysis(aid)
    if not item: return render_template("404.html"),404
    return render_template("result.html",item=item,warning=request.args.get("warning",""))

@app.get("/explanation/<int:aid>")
def explanation(aid):
    item=get_analysis(aid)
    if not item: return render_template("404.html"),404
    return render_template("explanation.html",item=item)

@app.get("/verify")
def verify():
    q=request.args.get("q","").strip()
    return render_template("verify.html",query=q,evidence=search_evidence(q) if q else [])

@app.get("/source-analysis")
def source_analysis():
    source=request.args.get("source","").strip()
    matches=[r for r in list_analyses(500) if source and source.casefold() in (r.get("source") or "").casefold()]
    return render_template("source_analysis.html",source=source,matches=matches,
       total=len(matches),fake=sum(r["prediction"]=="Likely Fake" for r in matches),
       real=sum(r["prediction"]=="Likely Real" for r in matches))

@app.get("/analytics")
def analytics():
    rows=list_analyses(500)
    return render_template("analytics.html",rows=rows[:20],total=len(rows),
      fake=sum(r["prediction"]=="Likely Fake" for r in rows),
      real=sum(r["prediction"]=="Likely Real" for r in rows),info=model_info())

@app.get("/history")
def history(): return render_template("history.html",rows=list_analyses(200))

@app.post("/history/delete/<int:aid>")
def history_delete(aid):
    delete_analysis(aid); flash("Analysis record deleted.","success")
    return redirect(url_for("history"))

@app.post("/feedback/<int:aid>")
def feedback(aid):
    if get_analysis(aid):
        add_feedback(aid,request.form.get("feedback_type","correction"),clean_text(request.form.get("details",""))[:2000])
        flash("Feedback saved for review; it is not automatically treated as ground truth.","success")
    return redirect(url_for("result",aid=aid))

@app.route("/duplicate",methods=["GET","POST"])
def duplicate():
    text=""; results=[]
    if request.method=="POST":
        text=clean_text(request.form.get("article_text",""))
        if text: results=find_similar(text)
    return render_template("duplicate.html",text=text,results=results)

@app.get("/model-performance")
def model_performance(): return render_template("model_performance.html",info=model_info(),ready=ready())

@app.get("/awareness")
def awareness(): return render_template("awareness.html")

@app.get("/about")
def about(): return render_template("about.html")

@app.get("/api/health")
def api_health(): return jsonify({"status":"ok","model_ready":ready(),"message":"Fake News Detection API is running"})

@app.post("/api/predict")
def api_predict():
    data=request.get_json(silent=True) or {}; text=clean_text(data.get("text",""))
    if not text: return jsonify({"error":"text is required"}),400
    if len(text)>MAX_TEXT_CHARS: return jsonify({"error":f"text must be at most {MAX_TEXT_CHARS} characters"}),413
    try:
        r=predict_text(text); m,v=load_artifacts(); why=explain(m,v,r["matrix"])
        aid=save_analysis(clean_text(data.get("title",""))[:300] or text[:100],text,r["prediction"],r["confidence"],
                          r["language"],r["translated"],why,clean_text(data.get("source",""))[:300],session.get("user_id"))
        return jsonify({"id":aid,"prediction":r["prediction"],"confidence":r["confidence"],"language":r["language"],
                        "translated":r["translated"],"warning":r["warning"],"explanation":why,
                        "disclaimer":"AI prediction is not independent fact verification."})
    except Exception as e: return jsonify({"error":str(e)}),503

@app.get("/api/model-info")
def api_model_info(): return jsonify({"model_ready":ready(),"metrics":model_info()})

@app.get("/api/history")
def api_history(): return jsonify(list_analyses(100))

@app.get("/report/<int:aid>.pdf")
def report(aid):
    item=get_analysis(aid)
    if not item: return render_template("404.html"),404
    return send_file(create_report(item),mimetype="application/pdf",as_attachment=True,download_name=f"fake_news_report_{aid}.pdf")

@app.errorhandler(404)
def missing(_): return render_template("404.html"),404

if __name__=="__main__": app.run(debug=True)
