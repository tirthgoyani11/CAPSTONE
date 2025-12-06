import os
import torch
from sentence_transformers import SentenceTransformer, util
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class ScoringEngine:
    def __init__(self, model_path=None):
        """
        Initialize the scoring engine.
        If model_path is provided, load the local model.
        """
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Loading model on {self.device}...")
        
        if model_path and os.path.exists(model_path):
            self.model = SentenceTransformer(model_path, device=self.device)
            print(f"Loaded local model from {model_path}")
        else:
            # Fallback (though user insists on local)
            print("Local model not found, downloading default...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2', device=self.device)

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
        # categorize skills for better context later
        self.skill_categories = {
            'languages': {'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift', 'go', 'rust', 'typescript', 'sql', 'r', 'matlab'},
            'web': {'react', 'angular', 'vue', 'node', 'flask', 'django', 'spring', 'asp.net', 'html', 'css', 'bootstrap', 'jquery', 'tailwind'},
            'data': {'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras', 'hadoop', 'spark', 'tableau', 'power bi', 'excel'},
            'cloud': {'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'terraform', 'ansible', 'circleci', 'git'},
            'db': {'mysql', 'postgresql', 'mongodb', 'oracle', 'redis', 'cassandra', 'elasticsearch', 'dynamodb'},
            'soft': {'communication', 'leadership', 'teamwork', 'agile', 'scrum', 'problem solving', 'time management', 'presentation'}
        }
        
        # Flatten for searching
        all_skills = set()
        for cat_skills in self.skill_categories.values():
            all_skills.update(cat_skills)

        found = set()
        lower_text = text.lower()
        
        # Regex for word boundary to avoid partial matches (e.g. 'go' in 'google')
        import re
        for skill in all_skills:
            # Escape skill for regex (e.g. c++)
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, lower_text):
                found.add(skill)
        
        return list(found)

    def analyze_candidate(self, cv_text, jd_text):
        """
        Extract skills from both, find gaps, and generate questions.
        """
        # Ensure categories are loaded
        if not hasattr(self, 'skill_categories'):
             self.extract_skills("") # Init categories
             
        cv_skills = set(self.extract_skills(cv_text))
        jd_skills = set(self.extract_skills(jd_text))
        
        missing = list(jd_skills - cv_skills)
        matching = list(jd_skills.intersection(cv_skills))
        
        questions = self.generate_interview_questions(missing)
        
        return {
            'cv_skills': list(cv_skills),
            'jd_skills': list(jd_skills),
            'missing': missing,
            'matching': matching,
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
        Compute a comprehensive score for the CV against the JD.
        """
        if weights is None:
            # Default weights
            weights = {
                'overall_similarity': 0.5,
                'skills': 0.3, # We will try to extract skills specifically if possible
                'experience': 0.2
            }
        
        # 1. Overall Semantic Match (The core "AI" score)
        overall_score = self.compute_similarity(cv_text, jd_text)
        
        # 2. Key Term Matching (Simple Hybrid Approach)
        # In a real scenario, we'd extract specific skills. 
        # Here we verify if critical terms in JD appear in CV (Exact Match boost)
        
        # Simple extraction of "keywords" from JD (e.g., capitalized words maybe? or just high relevance terms)
        # For now, let's treat the overall semantic score as the primary driver, 
        # but we can do a sectional score if we parsed the CV.
        
        from cv_parser import parse_cv_sections
        sections = parse_cv_sections(cv_text)
        
        # Skill Score: Compare CV 'skills' section specifically to JD
        if sections.get('skills') and len(sections['skills']) > 20: 
             skill_score = self.compute_similarity(sections['skills'], jd_text)
        else:
            # Fallback if no skills section detected, use overall
            skill_score = overall_score
            
        # Experience Score: Compare CV 'experience' section to JD
        if sections.get('experience') and len(sections['experience']) > 20:
            experience_score = self.compute_similarity(sections['experience'], jd_text)
        else:
            experience_score = overall_score

        # Weighted Total
        # Normalize scores (they are cosine sim -1 to 1, but usually 0 to 1 for text)
        overall_score = max(0, overall_score)
        skill_score = max(0, skill_score)
        experience_score = max(0, experience_score)
        
        total_score = (
            (overall_score * weights.get('overall_similarity', 0.5)) +
            (skill_score * weights.get('skills', 0.3)) +
            (experience_score * weights.get('experience', 0.2))
        )
        
        return {
            "total_score": round(total_score * 100, 2),
            "breakdown": {
                "semantic_match": round(overall_score * 100, 2),
                "skills_match": round(skill_score * 100, 2),
                "experience_match": round(experience_score * 100, 2)
            }
        }
