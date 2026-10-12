BASE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}Career Coach{% endblock %}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
  <div class="container">
    <a class="navbar-brand" href="{{ url_for('dashboard') }}">Career Coach</a>
    {% if current_user.is_authenticated %}
    <div class="ms-auto">
      <span class="text-light me-3">{{ current_user.name }}</span>
      <a class="btn btn-sm btn-outline-light" href="{{ url_for('logout') }}">Logout</a>
    </div>
    {% endif %}
  </div>
</nav>

<div class="container py-4">
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for category, msg in messages %}
      <div class="alert alert-{{ category }}">{{ msg }}</div>
    {% endfor %}
  {% endwith %}
  {% block content %}{% endblock %}
</div>
</body>
</html>
"""

LOGIN = """
{% extends "base.html" %}
{% block title %}Login{% endblock %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-5">
    <div class="card shadow-sm">
      <div class="card-body">
        <h4 class="mb-3">Login</h4>
        <form method="post">
          <div class="mb-3">
            <label class="form-label">Email</label>
            <input type="email" name="email" class="form-control" required>
          </div>
          <div class="mb-3">
            <label class="form-label">Password</label>
            <input type="password" name="password" class="form-control" required>
          </div>
          <button class="btn btn-dark w-100">Login</button>
        </form>
        <p class="mt-3 mb-0 text-center">
          New here? <a href="{{ url_for('register') }}">Create an account</a>
        </p>
      </div>
    </div>
  </div>
</div>
{% endblock %}
"""

REGISTER = """
{% extends "base.html" %}
{% block title %}Sign Up{% endblock %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-5">
    <div class="card shadow-sm">
      <div class="card-body">
        <h4 class="mb-3">Create Account</h4>
        <form method="post">
          <div class="mb-3">
            <label class="form-label">Full Name</label>
            <input type="text" name="name" class="form-control" required>
          </div>
          <div class="mb-3">
            <label class="form-label">Email</label>
            <input type="email" name="email" class="form-control" required>
          </div>
          <div class="mb-3">
            <label class="form-label">Password</label>
            <input type="password" name="password" class="form-control" minlength="6" required>
          </div>
          <button class="btn btn-dark w-100">Sign Up</button>
        </form>
        <p class="mt-3 mb-0 text-center">
          Already registered? <a href="{{ url_for('login') }}">Login</a>
        </p>
      </div>
    </div>
  </div>
</div>
{% endblock %}
"""

DASHBOARD = """
{% extends "base.html" %}
{% block title %}Dashboard{% endblock %}
{% block content %}
<h4 class="mb-4">Welcome, {{ current_user.name }}</h4>
<div class="row g-3">
  <div class="col-md-3">
    <div class="card h-100"><div class="card-body">
      <h6>My Profile</h6>
      <p class="text-muted small">
        {% if profile and profile.target_role %}
          Target: {{ profile.target_role }}
        {% else %}
          Target role and current skills
        {% endif %}
      </p>
      <a class="btn btn-sm btn-dark" href="{{ url_for('profile') }}">
        {% if profile %}Edit{% else %}Set up{% endif %}
      </a>
    </div></div>
  </div>
  <div class="col-md-3">
    <div class="card h-100"><div class="card-body">
      <h6>Resume Upload</h6>
      <p class="text-muted small">
        {% if resume %}
          {{ resume.file_name }}
        {% else %}
          Upload PDF or DOCX resume
        {% endif %}
      </p>
      <a class="btn btn-sm btn-dark" href="{{ url_for('upload') }}">
        {% if resume %}Re-upload{% else %}Upload{% endif %}
      </a>
    </div></div>
  </div>
  <div class="col-md-3">
    <div class="card h-100"><div class="card-body">
      <h6>ATS Score</h6>
      <p class="text-muted small">Resume score out of 100</p>
      {% if profile and resume %}
        <a class="btn btn-sm btn-dark" href="{{ url_for('analysis') }}">Run analysis</a>
      {% else %}
        <button class="btn btn-sm btn-secondary" disabled>Profile + resume needed</button>
      {% endif %}
    </div></div>
  </div>
  <div class="col-md-3">
    <div class="card h-100"><div class="card-body">
      <h6>Interview Prep</h6>
      <p class="text-muted small">Practice questions for your role</p>
      {% if profile and profile.target_role %}
        <a class="btn btn-sm btn-dark" href="{{ url_for('interview') }}">Practice</a>
      {% else %}
        <button class="btn btn-sm btn-secondary" disabled>Profile needed</button>
      {% endif %}
    </div></div>
  </div>
</div>

{% if resume %}
<div class="card mt-4">
  <div class="card-body">
    <h6 class="mb-3">Last Resume</h6>
    <p class="mb-1 small text-muted">Uploaded on {{ resume.uploaded_at }}</p>
    <a class="btn btn-sm btn-outline-dark" href="{{ url_for('resume_view') }}">View extracted data</a>
  </div>
</div>
{% endif %}
{% endblock %}
"""

PROFILE = """
{% extends "base.html" %}
{% block title %}My Profile{% endblock %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-7">
    <div class="card shadow-sm">
      <div class="card-body">
        <h5 class="mb-3">My Profile</h5>
        <form method="post">
          <div class="mb-3">
            <label class="form-label">Current Role</label>
            <input type="text" name="current_role" class="form-control"
                   value="{{ profile.current_role if profile else '' }}"
                   placeholder="e.g. Software Engineer / Student">
          </div>
          <div class="mb-3">
            <label class="form-label">Target Role</label>
            <select name="target_role" class="form-select" required>
              <option value="">-- select --</option>
              {% for role in roles %}
                <option value="{{ role }}"
                  {% if profile and profile.target_role == role %}selected{% endif %}>
                  {{ role }}
                </option>
              {% endfor %}
            </select>
          </div>
          <div class="mb-3">
            <label class="form-label">Experience (years)</label>
            <input type="number" step="0.5" min="0" name="experience_years" class="form-control"
                   value="{{ profile.experience_years if profile else '' }}" required>
            <div class="form-text">Enter 0 if you are a fresher. At 0 the scoring looks at the Projects section instead of Experience.</div>
          </div>
          <div class="mb-3">
            <label class="form-label">Current Skills</label>
            <textarea name="skills" class="form-control" rows="3"
                      placeholder="comma separated, e.g. python, sql, git">{{ profile.skills if profile else '' }}</textarea>
            <div class="form-text">Comma separated. This fills in automatically after you upload a resume.</div>
          </div>
          <button class="btn btn-dark">Save Profile</button>
          <a class="btn btn-link" href="{{ url_for('dashboard') }}">Cancel</a>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
"""

UPLOAD = """
{% extends "base.html" %}
{% block title %}Resume Upload{% endblock %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-7">
    <div class="card shadow-sm">
      <div class="card-body">
        <h5 class="mb-3">Upload Resume</h5>
        <form method="post" enctype="multipart/form-data">
          <div class="mb-3">
            <label class="form-label">Resume file</label>
            <input type="file" name="resume" class="form-control" accept=".pdf,.docx" required>
            <div class="form-text">PDF or DOCX, up to {{ max_mb }} MB. Scanned resumes are not supported.</div>
          </div>
          <button class="btn btn-dark">Upload and Extract</button>
          <a class="btn btn-link" href="{{ url_for('dashboard') }}">Cancel</a>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
"""

RESUME_VIEW = """
{% extends "base.html" %}
{% block title %}Extracted Data{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
  <h5 class="mb-0">{{ resume.file_name }}</h5>
  <a class="btn btn-sm btn-outline-dark" href="{{ url_for('dashboard') }}">Back</a>
</div>

<div class="row g-3">
  <div class="col-md-4">
    <div class="card h-100"><div class="card-body">
      <h6>Contact</h6>
      <p class="small mb-1">Email: {{ parsed.contact.email or '-' }}</p>
      <p class="small mb-1">Phone: {{ parsed.contact.phone or '-' }}</p>
      <p class="small mb-1">LinkedIn: {{ parsed.contact.linkedin or '-' }}</p>
      <p class="small mb-0">GitHub: {{ parsed.contact.github or '-' }}</p>
    </div></div>
  </div>
  <div class="col-md-4">
    <div class="card h-100"><div class="card-body">
      <h6>Sections Found</h6>
      {% for s in parsed.sections %}
        <span class="badge bg-success me-1 mb-1">{{ s }}</span>
      {% else %}
        <p class="small text-muted mb-0">No standard section heading detected.</p>
      {% endfor %}
      <p class="small text-muted mt-2 mb-0">
        Words: {{ parsed.word_count }} &middot;
        Bullets: {{ parsed.bullet_count }} &middot;
        With numbers: {{ parsed.quantified_bullets }}
      </p>
    </div></div>
  </div>
  <div class="col-md-4">
    <div class="card h-100"><div class="card-body">
      <h6>Skills Detected ({{ parsed.skills|length }})</h6>
      {% for s in parsed.skills %}
        <span class="badge bg-primary me-1 mb-1">{{ s }}</span>
      {% else %}
        <p class="small text-muted mb-0">No skill matched.</p>
      {% endfor %}
    </div></div>
  </div>
</div>

<div class="card mt-3">
  <div class="card-body">
    <h6>Raw Text</h6>
    <pre class="small bg-light p-3" style="max-height:400px;overflow:auto">{{ resume.raw_text }}</pre>
  </div>
</div>
{% endblock %}
"""

ANALYSIS = """
{% extends "base.html" %}
{% block title %}Analysis{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
  <div>
    <h5 class="mb-0">Resume Analysis</h5>
    <small class="text-muted">
      {{ resume.file_name }} &middot; Target: {{ profile.target_role }} &middot; {{ result.ats.mode }} mode
    </small>
  </div>
  <a class="btn btn-sm btn-outline-dark" href="{{ url_for('dashboard') }}">Back</a>
</div>

<div class="row g-3">
  <div class="col-md-5">
    <div class="card h-100"><div class="card-body">
      <h6 class="mb-3">ATS Score</h6>
      <div class="d-flex align-items-baseline mb-3">
        <span class="display-4 fw-bold
          {% if result.ats.total >= 75 %}text-success
          {% elif result.ats.total >= 50 %}text-warning
          {% else %}text-danger{% endif %}">{{ result.ats.total }}</span>
        <span class="text-muted ms-2">/ 100</span>
      </div>
      {% for b in result.ats.breakdown %}
        <div class="mb-2">
          <div class="d-flex justify-content-between small">
            <span>{{ b.name }}</span>
            <span>{{ b.score }}/{{ b.max }}</span>
          </div>
          <div class="progress" style="height:6px">
            <div class="progress-bar bg-dark" style="width: {{ (b.score / b.max * 100)|round(0, 'floor') }}%"></div>
          </div>
        </div>
      {% endfor %}
    </div></div>
  </div>

  <div class="col-md-7">
    <div class="card h-100"><div class="card-body">
      <h6 class="mb-3">What to Fix</h6>
      {% for note in result.ats.notes %}
        <div class="border-start border-3 border-warning ps-3 mb-3 small">{{ note }}</div>
      {% else %}
        <p class="small text-success mb-0">No major issues found.</p>
      {% endfor %}
    </div></div>
  </div>
</div>

<div class="card mt-3">
  <div class="card-body">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h6 class="mb-0">Skill Gap &mdash; {{ profile.target_role }}</h6>
      <span class="badge bg-dark fs-6">{{ result.gap.match_percent }}% match</span>
    </div>

    <p class="small mb-1 text-muted">You have</p>
    <div class="mb-3">
      {% for s in result.gap.matched %}
        <span class="badge bg-success me-1 mb-1">{{ s }}</span>
      {% else %}
        <span class="small text-muted">None matched.</span>
      {% endfor %}
    </div>

    <p class="small mb-1 text-muted">Missing &mdash; must have</p>
    <div class="mb-3">
      {% for s in result.gap.must_missing %}
        <span class="badge bg-danger me-1 mb-1">{{ s }}</span>
      {% else %}
        <span class="small text-success">All must-have skills covered.</span>
      {% endfor %}
    </div>

    <p class="small mb-1 text-muted">Missing &mdash; good to have</p>
    <div>
      {% for s in result.gap.good_missing %}
        <span class="badge bg-secondary me-1 mb-1">{{ s }}</span>
      {% else %}
        <span class="small text-success">All good-to-have skills covered.</span>
      {% endfor %}
    </div>
  </div>
</div>

{% if result.courses %}
<div class="card mt-3">
  <div class="card-body">
    <h6 class="mb-3">Suggested Courses</h6>
    <table class="table table-sm align-middle mb-0">
      <thead>
        <tr><th>Skill</th><th>Priority</th><th>Course</th><th>Source</th></tr>
      </thead>
      <tbody>
        {% for c in result.courses %}
        <tr>
          <td>{{ c.skill }}</td>
          <td>
            <span class="badge {% if c.priority == 'Must have' %}bg-danger{% else %}bg-secondary{% endif %}">
              {{ c.priority }}
            </span>
          </td>
          <td><a href="{{ c.url }}" target="_blank">{{ c.title }}</a></td>
          <td class="small text-muted">{{ c.source }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endif %}
{% endblock %}
"""

INTERVIEW = """
{% extends "base.html" %}
{% block title %}Interview Prep{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
  <div>
    <h5 class="mb-0">Interview Prep</h5>
    <small class="text-muted">
      {{ profile.target_role }} &middot;
      {% if profile.experience_years and profile.experience_years >= 1 %}
        {{ profile.experience_years }} years
      {% else %}
        Fresher
      {% endif %}
    </small>
  </div>
  <a class="btn btn-sm btn-outline-dark" href="{{ url_for('dashboard') }}">Back</a>
</div>

{% if feedback %}
<div class="card mb-3 border-dark">
  <div class="card-body">
    <div class="d-flex justify-content-between align-items-start mb-2">
      <h6 class="mb-0">Answer Feedback</h6>
      <span class="badge fs-6
        {% if feedback.score >= 7 %}bg-success
        {% elif feedback.score >= 4 %}bg-warning text-dark
        {% else %}bg-danger{% endif %}">{{ feedback.score }}/10</span>
    </div>
    <p class="small text-muted mb-2">{{ asked }}</p>
    <p class="small mb-1"><strong>Good:</strong> {{ feedback.good }}</p>
    <p class="small mb-2"><strong>Missing:</strong> {{ feedback.missing }}</p>
    <div class="bg-light p-3 small">
      <strong>Better answer</strong><br>{{ feedback.better_answer }}
    </div>
  </div>
</div>
{% endif %}

<div class="card mb-3">
  <div class="card-body d-flex justify-content-between align-items-center">
    <div>
      <h6 class="mb-1">
        {% if questions %}{{ questions|length }} questions ready{% else %}No questions yet{% endif %}
      </h6>
      <small class="text-muted">
        The model runs locally on CPU, so generating can take 30 to 60 seconds.
      </small>
    </div>
    <form method="post" action="{{ url_for('interview_generate') }}">
      <button class="btn btn-dark">
        {% if questions %}Generate new set{% else %}Generate questions{% endif %}
      </button>
    </form>
  </div>
</div>

{% for q in questions %}
<div class="card mb-2">
  <div class="card-body">
    <span class="badge bg-secondary mb-2">{{ q.type }}</span>
    <p class="mb-1">{{ loop.index }}. {{ q.question }}</p>
    {% if q.hint %}
      <p class="small text-muted mb-2">Hint: {{ q.hint }}</p>
    {% endif %}

    <a class="small" data-bs-toggle="collapse" href="#ans{{ loop.index }}">Write answer</a>
    <div class="collapse mt-2" id="ans{{ loop.index }}">
      <form method="post" action="{{ url_for('interview_answer') }}">
        <input type="hidden" name="question" value="{{ q.question }}">
        <textarea name="answer" class="form-control mb-2" rows="4"
                  placeholder="Type your answer here"></textarea>
        <button class="btn btn-sm btn-dark">Check my answer</button>
      </form>
    </div>
  </div>
</div>
{% endfor %}

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
{% endblock %}
"""

TEMPLATES = {
    "base.html": BASE,
    "login.html": LOGIN,
    "register.html": REGISTER,
    "dashboard.html": DASHBOARD,
    "profile.html": PROFILE,
    "upload.html": UPLOAD,
    "resume_view.html": RESUME_VIEW,
    "analysis.html": ANALYSIS,
    "interview.html": INTERVIEW,
}