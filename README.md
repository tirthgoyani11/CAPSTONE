# 🚀 NexGen ATS - AI-Powered Recruitment Platform

<div align="center">

![NexGen ATS](static/logo.png)

**Next-Generation Applicant Tracking System with AI-Powered CV Scoring**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.x-green.svg)](https://flask.palletsprojects.com)
[![AI](https://img.shields.io/badge/AI-Sentence%20Transformers-orange.svg)](https://www.sbert.net/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Architecture](#-architecture) • [API](#-api-endpoints) • [Contributing](#-contributing)

</div>

---

## 📋 Overview

**NexGen ATS** is a modern, AI-powered Applicant Tracking System designed to revolutionize the recruitment process. It leverages state-of-the-art Natural Language Processing (NLP) using Sentence Transformers to provide intelligent CV-to-Job Description matching, automated skills extraction, and comprehensive candidate management.

### 🎯 Why NexGen ATS?

- **🤖 AI-First Approach**: Uses semantic similarity (not just keyword matching) to find the best candidates
- **⚡ Real-Time Scoring**: Instant AI scoring of resumes against job descriptions
- **📊 Rich Analytics**: Visual dashboards with hiring funnel insights
- **🔐 Role-Based Access**: Separate portals for recruiters and candidates
- **☁️ Cloud-Ready**: One-click deployment to Render, Heroku, or any Docker host

---

## ✨ Features

### For Recruiters
| Feature | Description |
|---------|-------------|
| **🎯 Smart Job Posting** | Create detailed job descriptions with required skills and experience levels |
| **📄 Bulk CV Upload** | Upload multiple resumes at once with drag-and-drop support |
| **🧠 AI Scoring Engine** | Automatic scoring based on semantic similarity, skills match, and experience alignment |
| **👥 Talent Pool** | Central repository of all candidates with advanced filtering |
| **📅 Interview Scheduling** | Integrated interview management system |
| **📊 Analytics Dashboard** | Visual insights into hiring pipeline, conversion rates, and time-to-hire |
| **📝 Offer Management** | Generate and send professional offer letters |
| **🔍 Candidate Comparison** | Side-by-side comparison of top candidates |
| **📤 Data Export** | Export candidate data to CSV/Excel |

### For Candidates
| Feature | Description |
|---------|-------------|
| **🌐 Public Job Board** | Browse and search available positions |
| **📋 Easy Apply** | One-click application with resume upload |
| **👤 Profile Management** | Maintain profile with skills, experience, and education |
| **📈 Application Tracking** | Track status of all applications |

### AI Capabilities
- **Semantic Similarity Analysis** using `all-mpnet-base-v2` transformer model
- **Automatic Skills Extraction** across 7 categories (Programming, Web, Data Science, Cloud, Database, Mobile, Soft Skills)
- **Experience Parsing** with years of experience detection
- **Missing Skills Identification** for gap analysis
- **Auto-Generated Interview Questions** based on candidate profile

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              NexGen ATS Architecture                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                   │
│   │   Browser   │────▶│   Flask     │────▶│  Database   │                   │
│   │  (Jinja2)   │◀────│   Server    │◀────│  SQLite/    │                   │
│   └─────────────┘     └──────┬──────┘     │  PostgreSQL │                   │
│                              │            └─────────────┘                   │
│                              │                                               │
│                              ▼                                               │
│                    ┌─────────────────┐                                       │
│                    │  Scoring Engine │                                       │
│                    │  ┌───────────┐  │                                       │
│                    │  │ Sentence  │  │                                       │
│                    │  │Transformer│  │                                       │
│                    │  │(all-mpnet)│  │                                       │
│                    │  └───────────┘  │                                       │
│                    └─────────────────┘                                       │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        Route Modules                                 │   │
│   ├─────────────┬─────────────┬─────────────┬─────────────┬─────────────┤   │
│   │   auth.py   │  core.py    │talent_pool  │ analytics   │ interviews  │   │
│   │  (Login/   │(Dashboard,  │  (Search,   │  (Metrics,  │ (Schedule,  │   │
│   │  Register) │ Jobs, Apply)│  Filter)    │  Charts)    │  Manage)    │   │
│   └─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| **Backend** | Python 3.10+, Flask, Flask-Login |
| **AI/ML** | Sentence Transformers, PyTorch, scikit-learn |
| **Database** | SQLite (Development), PostgreSQL (Production) |
| **CV Parsing** | pdfplumber (PDF), python-docx (DOCX) |
| **Frontend** | Jinja2 Templates, Vanilla CSS, JavaScript |
| **Deployment** | Docker, Gunicorn, Render/Heroku Ready |

---

## 📦 Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Git

### Option 1: Local Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/nexgen-ats.git
cd nexgen-ats

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The application will be available at `http://localhost:5000`

### Option 2: Docker Deployment

```bash
# Build the Docker image
docker build -t nexgen-ats .

# Run the container
docker run -p 5000:5000 -e PORT=5000 nexgen-ats
```

### Option 3: Cloud Deployment (Render)

1. Fork this repository
2. Create a new Web Service on [Render](https://render.com)
3. Connect your GitHub repository
4. Set environment variables:
   - `PORT`: 10000
   - `DATABASE_URL`: Your PostgreSQL connection string (optional)
   - `SECRET_KEY`: A secure random string
5. Deploy!

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask session secret key | `dev-secret-key-change-in-prod` |
| `DATABASE_URL` | PostgreSQL connection string | SQLite (`ats.db`) |
| `AI_MODEL_NAME` | Sentence Transformer model | `all-mpnet-base-v2` |
| `PORT` | Server port | `5000` |

### Database Setup

**SQLite (Default - No Configuration Needed)**
```python
# Automatically creates ats.db in project root
```

**PostgreSQL (Production)**
```bash
export DATABASE_URL="postgresql://user:password@host:5432/dbname"
```

---

## 🚀 Usage

### Quick Start Guide

1. **Start the Server**
   ```bash
   python app.py
   ```

2. **Register an Account**
   - Navigate to `http://localhost:5000/register`
   - Create a recruiter account (set role to 'recruiter')

3. **Post a Job**
   - Go to Dashboard → Add New Job
   - Enter job title and detailed description
   - Include required skills and experience

4. **Upload Candidates**
   - Navigate to the job listing
   - Use drag-and-drop to upload CVs (PDF/DOCX)
   - AI automatically scores candidates

5. **Review & Compare**
   - View ranked candidates by AI score
   - Compare top candidates side-by-side
   - Schedule interviews directly

### Demo Credentials

For testing purposes:
```
Recruiter:
  Email: recruiter@demo.com
  Password: demo123

Candidate:
  Email: candidate@demo.com
  Password: demo123
```

---

## 📚 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/login` | User login |
| GET/POST | `/register` | User registration |
| GET | `/logout` | User logout |

### Jobs (Core)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Home/Dashboard |
| GET | `/dashboard` | Recruiter dashboard |
| GET/POST | `/add-job` | Create new job |
| GET | `/job/<id>` | View job details |
| POST | `/job/<id>/upload` | Upload CVs to job |
| GET | `/job/<id>/candidates` | List candidates for job |

### Candidates
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/candidate/<id>` | View candidate details |
| POST | `/candidate/<id>/status` | Update candidate status |
| GET | `/candidate/<id>/notes` | Get candidate notes |
| POST | `/candidate/<id>/notes` | Add candidate notes |

### Talent Pool
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/talent-pool` | Browse all candidates |
| GET | `/talent-pool/search` | Search candidates |
| GET | `/compare` | Compare candidates |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics` | Analytics dashboard |
| GET | `/analytics/data` | Get analytics JSON |

### Public Job Board
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/jobs` | Public job listings |
| GET | `/jobs/<id>` | Public job detail |
| POST | `/easy-apply/<id>` | Apply to job |

---

## 📁 Project Structure

```
nexgen-ats/
├── 📄 app.py                 # Flask application entry point
├── 📄 database.py            # Database models & initialization
├── 📄 scoring_engine.py      # AI scoring engine (Sentence Transformers)
├── 📄 cv_parser.py           # PDF/DOCX text extraction
├── 📄 decorators.py          # Auth decorators (recruiter_required)
├── 📄 requirements.txt       # Python dependencies
├── 📄 Dockerfile             # Docker configuration
├── 📄 Procfile               # Heroku/Render deployment
│
├── 📂 routes/                # Flask Blueprints
│   ├── auth.py               # Authentication routes
│   ├── core.py               # Main application routes
│   ├── talent_pool.py        # Talent pool management
│   ├── analytics.py          # Analytics & reporting
│   ├── interviews.py         # Interview scheduling
│   ├── settings.py           # User settings
│   └── export_routes.py      # Data export functionality
│
├── 📂 templates/             # Jinja2 HTML templates
│   ├── layout.html           # Base template
│   ├── dashboard.html        # Recruiter dashboard
│   ├── job_board.html        # Public job listings
│   ├── talent_pool.html      # Candidate search
│   ├── analytics.html        # Analytics dashboard
│   └── ...                   # Other templates
│
├── 📂 static/                # Static assets
│   ├── style.css             # Main stylesheet
│   ├── script.js             # JavaScript functionality
│   └── logo.png              # Application logo
│
├── 📂 models/                # AI model cache
│   └── nexgen_cv_engine/     # Cached Sentence Transformer
│
├── 📂 uploads/               # Uploaded CV storage
├── 📂 tests/                 # Test suite
└── 📂 utils/                 # Utility functions
```

---

## 🧠 AI Scoring Engine

### How It Works

The NexGen Scoring Engine uses a sophisticated **5-dimensional scoring model** with intelligent adjustments:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    NexGen Smart Score Algorithm                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Base Score = Σ (Component × Weight)                                   │
│                                                                         │
│   ┌─────────────────┬────────┬────────────────────────────────────┐    │
│   │ Component       │ Weight │ What it measures                   │    │
│   ├─────────────────┼────────┼────────────────────────────────────┤    │
│   │ Semantic Match  │  35%   │ Deep contextual fit via AI         │    │
│   │ Skills Match    │  30%   │ Core + nice-to-have skills         │    │
│   │ Experience      │  20%   │ Years vs requirements              │    │
│   │ Education       │  10%   │ Degree level alignment             │    │
│   │ Recency         │   5%   │ Current employment status          │    │
│   └─────────────────┴────────┴────────────────────────────────────┘    │
│                                                                         │
│   Final Score = Base + Confidence Boost - Critical Penalty             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Scoring Components Explained

#### 1. Semantic Similarity (35%)
- Uses Sentence Transformers (`all-mpnet-base-v2`) to create embeddings
- Computes cosine similarity between CV and Job Description
- Captures **contextual meaning** beyond simple keyword matching
- Understands synonyms, related concepts, and industry terminology

#### 2. Skills Match (30%)
Advanced multi-factor skill scoring:

| Factor | Description | Bonus |
|--------|-------------|-------|
| **Core Skills** | Must-have/required skills (70% of skill score) | - |
| **Nice-to-Have** | Preferred/bonus skills (30% of skill score) | - |
| **Skill Depth** | Multiple mentions of a skill | +2% per skill (max 10%) |
| **Transferable Skills** | Related technologies (e.g., React → Vue) | +3% per skill (max 15%) |

#### 3. Experience Alignment (20%)
Intelligent experience matching with JD parsing:

| Scenario | Score | Label |
|----------|-------|-------|
| Within required range | 100% | Perfect Match |
| 1 year under | 75% | Slightly Under |
| 2 years under | 55% | Under-Qualified |
| 1-3 years over | 90% | Slightly Over |
| 4+ years over | 75% | Over-Qualified |

#### 4. Education Fit (10%)
Automatic degree detection and scoring:

| Level | Score |
|-------|-------|
| PhD/Doctorate | 100% |
| Master's/MBA | 90% |
| Bachelor's | 75% |
| Associate/Diploma | 60% |
| High School | 40% |

#### 5. Recency Factor (5%)
Rewards active professionals:

| Status | Score |
|--------|-------|
| Currently Employed | 100% |
| Recently Active (2 years) | 85% |
| Employment Gap | 65% |

### Intelligent Adjustments

**Confidence Boost**: When 3+ signals are strong (>70%), adds up to +5%

**Critical Penalty**: Missing >70% core skills applies -10% penalty

### Grade System

| Score | Grade | Recommendation |
|-------|-------|----------------|
| 85%+ | A+ | Excellent Match - Priority Interview |
| 75-84% | A | Strong Match - Recommended |
| 65-74% | B+ | Good Match - Consider |
| 55-64% | B | Moderate Match - Review |
| 45-54% | C | Partial Match - Optional |
| <45% | D | Weak Match - Not Recommended |

### Skill Categories

| Category | Examples |
|----------|----------|
| **Languages** | Python, Java, JavaScript, C++, Rust, Go |
| **Web** | React, Angular, Vue, Flask, Django, Node.js |
| **Data Science** | Pandas, NumPy, TensorFlow, PyTorch, Spark |
| **Cloud** | AWS, Azure, GCP, Docker, Kubernetes, Terraform |
| **Databases** | PostgreSQL, MongoDB, Redis, Elasticsearch |
| **Mobile** | Android, iOS, Flutter, React Native |
| **Soft Skills** | Leadership, Communication, Agile, Scrum |

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=. tests/

# Run specific test file
python -m pytest tests/test_scoring.py
```

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines

- Follow PEP 8 style guide for Python
- Write docstrings for all functions
- Add unit tests for new features
- Update documentation as needed

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| CV Processing | ~2-3 seconds per resume |
| Model Loading | ~5-10 seconds (first request) |
| Memory Usage | ~500MB (with model loaded) |
| Concurrent Users | 50+ (with Gunicorn) |

---

## 🔒 Security

- **Password Hashing**: Werkzeug security utilities
- **Session Management**: Flask-Login with secure cookies
- **File Validation**: Extension and size limits on uploads
- **SQL Injection**: Parameterized queries throughout
- **CSRF Protection**: Available via Flask-WTF (optional)

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Sentence Transformers](https://www.sbert.net/) for the amazing NLP models
- [Flask](https://flask.palletsprojects.com/) for the lightweight web framework
- [pdfplumber](https://github.com/jsvine/pdfplumber) for PDF text extraction

---

## 📧 Contact

**Project Maintainer**: Tirth Goyani  
**Email**: tirthgoyani123@example.com  
**Project Link**: [https://github.com/tirthgoyani11/nexgen-ats](https://github.com/tirthgoyani11/nexgen-ats)

---

<div align="center">

**⭐ Star this repository if you find it helpful! ⭐**

Made with ❤️ for the recruitment industry

</div>
