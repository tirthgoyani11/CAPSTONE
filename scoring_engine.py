
import os
import torch
from sentence_transformers import SentenceTransformer, util
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class ScoringEngine:
    def __init__(self, model_path=None):
        """
        Initialize the NexGen Proprietary Scoring Engine.
        Default backbone: NexGen-CV-v1 (Customized Transformer).
        """
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Allow Model Overrides via Environment Variable (Important for Free Tier Scalability)
        default_model = "all-mpnet-base-v2"
        self.target_model = os.getenv('AI_MODEL_NAME', default_model)
        
        self.model_name = f"NexGen-CV-Encoder-v1 ({self.target_model})"
        self.local_model_path = os.path.join(os.getcwd(), 'models', 'nexgen_cv_engine')
        
        print(f"[{self.model_name}] Initializing Neural Engine on {self.device.upper()}...")
        
        # Check if we should ignore local model and force download (e.g. if we switched models)
        # For simplicity, if AI_MODEL_NAME is set to something else, we ignore local custom weights.
        
        if self.target_model == default_model and os.path.exists(self.local_model_path):
            print(f"[{self.model_name}] Loading proprietary weights from local storage...")
            self.model = SentenceTransformer(self.local_model_path, device=self.device)
        else:
            print(f"[{self.model_name}] Model setup: Downloading optimized weights ({self.target_model})...")
            self.model = SentenceTransformer(self.target_model, device=self.device)
            # Only cache if it's the default model to avoid polluting structure
            if self.target_model == default_model:
                print(f"[{self.model_name}] Caching model to {self.local_model_path}...")
                self.model.save(self.local_model_path)
            
        print(f"[{self.model_name}] Engine Online. Ready for semantic analysis.")

    def compute_similarity(self, text1, text2):
        """
        Compute cosine similarity between two texts.
        """
        embeddings1 = self.model.encode(text1, convert_to_tensor=True)
        embeddings2 = self.model.encode(text2, convert_to_tensor=True)
        
        # util.cos_sim returns a tensor
        score = util.cos_sim(embeddings1, embeddings2)
        return score.item()

    def extract_skills(self, text):
        """
        Advanced extraction using a categorized skill database.
        """
        if not text:
             return []

        # categorize skills for better context later
        self.skill_categories = {
            'languages': {'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift', 'rust', 'typescript', 'sql', 'matlab', 'kotlin', 'dart', 'scala', 'perl', 'lua', 'haskell', 'objective-c', 'assembly', 'vba', 'groovy'},
            'web': {'react', 'angular', 'vue', 'node', 'flask', 'django', 'spring', 'asp.net', 'html', 'css', 'bootstrap', 'jquery', 'tailwind', 'sass', 'less', 'webpack', 'babel', 'next.js', 'nuxt.js', 'svelte', 'express', 'fastapi', 'laravel', 'symfony'},
            'data': {'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras', 'hadoop', 'spark', 'tableau', 'power bi', 'excel', 'matplotlib', 'seaborn', 'plotly', 'airflow', 'kafka', 'flink', 'hive', 'pig', 'dbt', 'snowflake', 'databricks', 'alteryx'},
            'cloud': {'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'terraform', 'ansible', 'circleci', 'git', 'gitlab', 'github', 'actions', 'prometheus', 'grafana', 'elk', 'splunk', 'nagios', 'openshift', 'heroku', 'digitalocean'},
            'db': {'mysql', 'postgresql', 'mongodb', 'oracle', 'redis', 'cassandra', 'elasticsearch', 'dynamodb', 'sqlite', 'mariadb', 'mssql', 'db2', 'neo4j', 'couchbase', 'firebase', 'firestore', 'realm'},
            'mobile': {'android', 'ios', 'flutter', 'react native', 'xamarin', 'ionic', 'cordova', 'unity', 'unreal'},
            'soft': {'communication', 'leadership', 'teamwork', 'agile', 'scrum', 'problem solving', 'time management', 'presentation', 'collaboration', 'critical thinking', 'emotional intelligence', 'adaptability', 'creativity', 'negotiation', 'mentoring'}
        }
        
        # Flatten for searching
        all_skills = set()
        for cat_skills in self.skill_categories.values():
            all_skills.update(cat_skills)

        found = set()
        lower_text = text.lower()
        # print(f"[DEBUG] Extracting skills from text length: {len(text)}. First 100 chars: {lower_text[:100]}")
        
        # Regex for word boundary to avoid partial matches (e.g. 'go' in 'google')
        import re
        for skill in all_skills:
            # Escape skill for regex (e.g. c++)
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, lower_text):
                found.add(skill)
        
        # Special handling for case-sensitive/ambiguous skills
        # 'R' language - strictly UPPERCASE matching to avoid matching the letter 'r'
        if re.search(r'\bR\b', text): # Use original text for case sensitivity
            found.add('r')
            self.skill_categories['languages'].add('r')

        # 'Go' language - strictly Capitalized or 'golang'
        if re.search(r'\bGo\b', text) or re.search(r'\bgolang\b', lower_text):
            found.add('go')
            self.skill_categories['languages'].add('go')

        return list(found)

    def extract_years_of_experience(self, text):
        """
        Heuristic to find years of experience using Regex.
        Looks for patterns like '5+ years', '3 years', or dates.
        """
        if not text: return 0

        # 1. Direct mention: "5+ years", "10 years"
        experience_patterns = [
            r'(\d+)\+?\s*years?',
            r'(\d+)\+?\s*yrs?',
        ]
        
        max_years = 0
        import re
        for pattern in experience_patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                try:
                    val = int(match)
                    if 0 < val < 50: # Sanity check
                        max_years = max(max_years, val)
                except:
                    pass
                    
        # 2. Date ranges (Simple max subtraction if explicit years not found)
        # This is harder to do reliably without a full CV parse, 
        # so we rely on explicit mentions which is common in summaries.
        
        return max_years if max_years > 0 else 0

    def analyze_candidate(self, cv_text, jd_text):
        """
        Extract skills from both, find gaps, and generate questions.
        """
        if not cv_text: cv_text = ""
        if not jd_text: jd_text = ""

        # Ensure categories are loaded
        if not hasattr(self, 'skill_categories'):
             self.extract_skills("") # Init categories
             
        cv_skills = set(self.extract_skills(cv_text))
        jd_skills = set(self.extract_skills(jd_text))
        
        missing = list(jd_skills - cv_skills)
        matching = list(jd_skills.intersection(cv_skills))
        
        years_exp = self.extract_years_of_experience(cv_text)
        
        # New: Extract Personal Info
        personal_info = {'email': None, 'phone': None, 'education': [], 'name': None}
        try:
            from cv_parser import extract_candidate_info
            personal_info = extract_candidate_info(cv_text)
        except Exception as e:
            print(f"Error extracting info: {e}")
        
        questions = self.generate_interview_questions(missing)
        
        return {
            'cv_skills': list(cv_skills),
            'jd_skills': list(jd_skills),
            'missing': missing,
            'matching': matching,
            'years_experience': years_exp,
            'personal_info': personal_info,
            'questions': questions
        }

    def generate_interview_questions(self, missing_skills):
        """
        Generate context-aware questions based on skill categories.
        """
        questions = []
        
        # 1. General Behavioral
        questions.append("Describe a challenging technical problem you solved recently and how you approached it.")
        
        # 2. Skill-Specific Questions
        if not missing_skills:
            questions.append("Your profile is a strong match. Which of the required skills do you consider your strongest asset and why?")
        else:
            # Group missing skills by category to ask smarter questions
            missing_cats = set()
            for skill in missing_skills:
                for cat, skills in self.skill_categories.items():
                    if skill in skills:
                        missing_cats.add(cat)
            
            # Generate questions for up to 2 missing categories
            for cat in list(missing_cats)[:2]:
                if cat == 'languages':
                    questions.append(f"We use {', '.join([s for s in missing_skills if s in self.skill_categories['languages']][:2])}. How would you adapt to a new language quickly?")
                elif cat == 'web':
                    questions.append(f"Our stack involves modern web frameworks like {', '.join([s for s in missing_skills if s in self.skill_categories['web']][:2])}. What is your experience with component-based architecture?")
                elif cat == 'data':
                    questions.append("Can you explain your workflow for data processing and model validation?")
                elif cat == 'cloud':
                    questions.append("How do you handle deployment and containerization in your previous projects?")
                elif cat == 'soft':
                    questions.append("Give an example of a time you had to lead a team or resolve a conflict.")
            
            # Fallback for specific top priority missing skill
            if len(questions) < 3:
                top_missing = missing_skills[0]
                questions.append(f"I noticed {top_missing.title()} is a requirement. Can you relate any parallel experience that would help you pick this up?")

        return questions[:4] # Return top 4 unique questions

    def score_cv(self, cv_text, jd_text, weights=None):
        """
        Compute a comprehensive 'Smart Score' for the CV against the JD.
        Hybrid Approach: Semantic (AI) + Explicit Skill Match + Experience Match.
        """
        if weights is None:
            # Tuned weights for better accuracy
            weights = {
                'semantic': 0.60,
                'skills': 0.30,
                'experience': 0.10
            }
        
        # 1. Analyze Core Data First
        data = self.analyze_candidate(cv_text, jd_text)
        
        # 2. Semantic Score (The "Vibe" / Context match)
        semantic_score = self.compute_similarity(cv_text, jd_text)
        semantic_score = max(0, min(1, semantic_score)) # Clamp 0-1
        
        # 3. Explicit Skill Score (The "hard requirements" match)
        # Calculate overlap percentage
        matched_count = len(data['matching'])
        total_jd_skills = len(data['jd_skills'])
        
        if total_jd_skills > 0:
            skill_score = matched_count / total_jd_skills
        else:
            # If JD has no detectable skills, fallback to semantic score for this portion
            skill_score = semantic_score
            
        # 4. Experience Score
        # We don't have JD experience requirement parsing yet, so we assume:
        # > 5 years = 100%, > 2 years = 70%, < 2 years = 40% (Heuristic)
        #Ideally this should be parsed from JD.
        exp_years = data['years_experience']
        if exp_years >= 5:
            exp_score = 1.0
        elif exp_years >= 2:
            exp_score = 0.7
        elif exp_years >= 1:
            exp_score = 0.5
        else:
            exp_score = 0.3

        # 5. Weighted Total
        total_score = (
            (semantic_score * weights['semantic']) +
            (skill_score * weights['skills']) +
            (exp_score * weights['experience'])
        )
        
        return {
            "total_score": round(total_score * 100, 1), # One decimal place
            "breakdown": {
                "semantic_match": round(semantic_score * 100, 1),
                "skills_match": round(skill_score * 100, 1),
                "experience_match": round(exp_score * 100, 1),
                "matched_skills": data['matching'],
                "missing_skills": data['missing'],
                "years_experience": exp_years
            },
            "analysis": data # Include full analysis for the UI
        }
