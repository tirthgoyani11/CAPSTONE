
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
        
        # New: Extract Personal Info with robust error handling
        default_info = {'email': None, 'phone': None, 'education': [], 'name': None, 'certifications': []}
        personal_info = default_info.copy()
        try:
            from cv_parser import extract_candidate_info
            extracted = extract_candidate_info(cv_text)
            if extracted and isinstance(extracted, dict):
                # Safely merge, keeping defaults for missing keys
                for key in default_info:
                    personal_info[key] = extracted.get(key, default_info[key])
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

    def _extract_required_experience(self, jd_text):
        """
        Parse required years of experience from job description.
        Returns (min_years, max_years) tuple.
        """
        import re
        if not jd_text:
            return (0, 0)
        
        lower_jd = jd_text.lower()
        
        # Pattern: "3-5 years", "3 to 5 years"
        range_pattern = r'(\d+)\s*[-to]+\s*(\d+)\s*(?:\+)?\s*years?'
        range_match = re.search(range_pattern, lower_jd)
        if range_match:
            return (int(range_match.group(1)), int(range_match.group(2)))
        
        # Pattern: "5+ years", "minimum 5 years", "at least 5 years"
        min_pattern = r'(?:minimum|at least|min\.?)?\s*(\d+)\s*\+?\s*years?'
        min_match = re.search(min_pattern, lower_jd)
        if min_match:
            years = int(min_match.group(1))
            return (years, years + 3)  # Assume +3 years range
        
        # Default: entry-level friendly
        return (0, 0)

    def _calculate_skill_score_advanced(self, cv_skills, jd_skills, cv_text, jd_text):
        """
        Advanced skill scoring with category weighting and partial matches.
        - Core/must-have skills weighted higher
        - Transferable skills get partial credit
        - Skill depth analysis (mentions frequency)
        """
        if not jd_skills:
            return 1.0, [], {}  # No requirements = perfect match
        
        import re
        matched = set(cv_skills).intersection(set(jd_skills))
        missing = set(jd_skills) - set(cv_skills)
        
        # Categorize skills by importance (inferred from JD context)
        core_keywords = ['required', 'must have', 'essential', 'mandatory', 'strong']
        nice_keywords = ['preferred', 'nice to have', 'bonus', 'plus', 'ideal']
        
        lower_jd = jd_text.lower()
        
        # Determine if skill is core or nice-to-have
        core_skills = set()
        nice_skills = set()
        
        for skill in jd_skills:
            # Check context around skill mention
            skill_idx = lower_jd.find(skill.lower())
            if skill_idx != -1:
                context = lower_jd[max(0, skill_idx-50):skill_idx+50]
                if any(kw in context for kw in core_keywords):
                    core_skills.add(skill)
                elif any(kw in context for kw in nice_keywords):
                    nice_skills.add(skill)
                else:
                    core_skills.add(skill)  # Default to core
            else:
                core_skills.add(skill)
        
        # Calculate weighted score
        core_matched = len(matched.intersection(core_skills))
        core_total = len(core_skills) if core_skills else 1
        nice_matched = len(matched.intersection(nice_skills))
        nice_total = len(nice_skills) if nice_skills else 1
        
        # Core skills: 70% weight, Nice-to-have: 30% weight
        if nice_skills:
            skill_score = (core_matched / core_total) * 0.7 + (nice_matched / nice_total) * 0.3
        else:
            skill_score = core_matched / core_total
        
        # Skill depth bonus: frequency of skill mentions in CV (up to 10% bonus)
        depth_bonus = 0
        lower_cv = cv_text.lower()
        for skill in matched:
            count = len(re.findall(r'\b' + re.escape(skill) + r'\b', lower_cv))
            if count >= 3:
                depth_bonus += 0.02  # 2% per deeply mentioned skill
        depth_bonus = min(depth_bonus, 0.10)  # Cap at 10%
        
        # Transferable skills: partial credit for related skills
        transferable_bonus = 0
        skill_families = {
            'python': ['java', 'ruby', 'php'],
            'react': ['angular', 'vue', 'svelte'],
            'aws': ['azure', 'gcp'],
            'postgresql': ['mysql', 'mssql', 'oracle'],
            'docker': ['kubernetes', 'podman'],
            'tensorflow': ['pytorch', 'keras'],
        }
        
        for missing_skill in missing:
            for primary, related in skill_families.items():
                if missing_skill == primary and any(r in cv_skills for r in related):
                    transferable_bonus += 0.03  # 3% credit for related skill
                elif missing_skill in related and primary in cv_skills:
                    transferable_bonus += 0.03
        transferable_bonus = min(transferable_bonus, 0.15)  # Cap at 15%
        
        final_score = min(1.0, skill_score + depth_bonus + transferable_bonus)
        
        breakdown = {
            'core_skills_matched': core_matched,
            'core_skills_total': len(core_skills),
            'nice_skills_matched': nice_matched,
            'nice_skills_total': len(nice_skills),
            'depth_bonus': round(depth_bonus * 100, 1),
            'transferable_bonus': round(transferable_bonus * 100, 1)
        }
        
        return final_score, list(missing), breakdown

    def _calculate_experience_score(self, cv_years, jd_min, jd_max):
        """
        Calculate experience score with nuanced matching.
        - Perfect range match: 100%
        - Slightly under: graduated penalty
        - Over-qualified: slight penalty (may leave soon)
        """
        if jd_min == 0 and jd_max == 0:
            # No requirement specified - use seniority tiers
            if cv_years >= 7:
                return 1.0, 'Senior'
            elif cv_years >= 4:
                return 0.85, 'Mid-Level'
            elif cv_years >= 1:
                return 0.70, 'Junior'
            else:
                return 0.50, 'Entry-Level'
        
        # Within range: perfect score
        if jd_min <= cv_years <= jd_max:
            return 1.0, 'Perfect Match'
        
        # Under-qualified: graduated penalty
        if cv_years < jd_min:
            gap = jd_min - cv_years
            if gap <= 1:
                return 0.75, 'Slightly Under'
            elif gap <= 2:
                return 0.55, 'Under-Qualified'
            else:
                return 0.35, 'Significantly Under'
        
        # Over-qualified: slight penalty
        if cv_years > jd_max:
            overage = cv_years - jd_max
            if overage <= 3:
                return 0.90, 'Slightly Over'
            else:
                return 0.75, 'Over-Qualified'
        
        return 0.5, 'Unknown'

    def _calculate_education_score(self, cv_text):
        """
        Score based on education level detected.
        """
        import re
        lower_cv = cv_text.lower()
        
        # Education hierarchy (patterns ordered by priority - highest first)
        education_levels = [
            (r'\b(ph\.?d\.?|doctorate|doctoral|doctor of)\b', 1.0, 'PhD'),
            (r'\b(masters?|m\.?s\.?|m\.?sc\.?|mba|m\.?tech|m\.?eng|master\'?s?)\b', 0.90, 'Masters'),
            (r'\b(bachelors?|b\.?s\.?|b\.?sc\.?|b\.?tech|b\.?e\.?|b\.?a\.?|undergraduate|bachelor\'?s?)\b', 0.75, 'Bachelors'),
            (r'\b(associate|diploma|certification|certified|certificate)\b', 0.60, 'Associate/Diploma'),
            (r'\b(high school|secondary|ged|hsc|12th)\b', 0.40, 'High School'),
        ]
        
        for pattern, score, level in education_levels:
            if re.search(pattern, lower_cv):
                return score, level
        
        return 0.50, 'Not Specified'

    def _calculate_recency_score(self, cv_text):
        """
        Bonus for recent/current employment and up-to-date skills.
        """
        import re
        from datetime import datetime
        
        lower_cv = cv_text.lower()
        current_year = datetime.now().year
        
        # Check for current employment
        current_patterns = [r'\b(present|current|ongoing|now)\b', r'\b202[4-9]\b', r'\b203\d\b']
        is_current = any(re.search(p, lower_cv) for p in current_patterns)
        
        # Check for recent years
        recent_years = [str(y) for y in range(current_year - 2, current_year + 1)]
        has_recent = any(year in cv_text for year in recent_years)
        
        if is_current and has_recent:
            return 1.0, 'Currently Employed'
        elif has_recent:
            return 0.85, 'Recently Active'
        else:
            return 0.65, 'Gap Detected'

    def score_cv(self, cv_text, jd_text, weights=None):
        """
        Compute a comprehensive 'Smart Score' for the CV against the JD.
        
        Enhanced Multi-Dimensional Scoring:
        - Semantic Similarity (35%): Deep contextual understanding via transformers
        - Skills Match (30%): Core vs nice-to-have, depth, transferable skills
        - Experience Alignment (20%): Range matching with over/under qualification handling
        - Education Fit (10%): Degree level matching
        - Recency Factor (5%): Current employment and recent activity
        
        Total = Weighted sum with intelligent adjustments
        """
        # Default weights for 5-dimensional scoring
        default_weights = {
            'semantic': 0.35,
            'skills': 0.30,
            'experience': 0.20,
            'education': 0.10,
            'recency': 0.05
        }
        
        # Merge provided weights with defaults (handles legacy 3-key weights)
        if weights is None:
            weights = default_weights
        else:
            # Fill in any missing keys from defaults
            for key in default_weights:
                if key not in weights:
                    weights[key] = default_weights[key]
        
        # 1. Analyze Core Data
        data = self.analyze_candidate(cv_text, jd_text)
        
        # 2. Semantic Score (Contextual/Cultural Fit)
        semantic_score = self.compute_similarity(cv_text, jd_text)
        semantic_score = max(0, min(1, semantic_score))
        
        # 3. Advanced Skill Scoring
        skill_score, missing_skills, skill_breakdown = self._calculate_skill_score_advanced(
            data['cv_skills'], data['jd_skills'], cv_text, jd_text
        )
        
        # 4. Experience Score with JD parsing
        jd_min, jd_max = self._extract_required_experience(jd_text)
        cv_years = data['years_experience']
        exp_score, exp_label = self._calculate_experience_score(cv_years, jd_min, jd_max)
        
        # 5. Education Score
        edu_score, edu_level = self._calculate_education_score(cv_text)
        
        # 6. Recency Score
        recency_score, recency_label = self._calculate_recency_score(cv_text)
        
        # 7. Calculate Weighted Total
        raw_total = (
            (semantic_score * weights['semantic']) +
            (skill_score * weights['skills']) +
            (exp_score * weights['experience']) +
            (edu_score * weights['education']) +
            (recency_score * weights['recency'])
        )
        
        # 8. Apply Confidence Adjustments
        # Boost if multiple strong signals align
        confidence_signals = sum([
            semantic_score > 0.7,
            skill_score > 0.7,
            exp_score > 0.8,
            edu_score > 0.7
        ])
        
        if confidence_signals >= 3:
            confidence_boost = 0.05  # 5% boost for strong alignment
        elif confidence_signals >= 2:
            confidence_boost = 0.02  # 2% boost
        else:
            confidence_boost = 0
        
        # Penalty for critical gaps
        core_skill_ratio = skill_breakdown.get('core_skills_matched', 0) / max(skill_breakdown.get('core_skills_total', 1), 1)
        if core_skill_ratio < 0.3:
            critical_penalty = 0.10  # 10% penalty for missing >70% core skills
        elif core_skill_ratio < 0.5:
            critical_penalty = 0.05  # 5% penalty
        else:
            critical_penalty = 0
        
        final_score = max(0, min(1, raw_total + confidence_boost - critical_penalty))
        
        # 9. Generate Match Grade
        if final_score >= 0.85:
            grade = 'A+'
            recommendation = 'Excellent Match - Priority Interview'
        elif final_score >= 0.75:
            grade = 'A'
            recommendation = 'Strong Match - Recommended'
        elif final_score >= 0.65:
            grade = 'B+'
            recommendation = 'Good Match - Consider'
        elif final_score >= 0.55:
            grade = 'B'
            recommendation = 'Moderate Match - Review'
        elif final_score >= 0.45:
            grade = 'C'
            recommendation = 'Partial Match - Optional'
        else:
            grade = 'D'
            recommendation = 'Weak Match - Not Recommended'
        
        return {
            "total_score": round(final_score * 100, 1),
            "grade": grade,
            "recommendation": recommendation,
            "breakdown": {
                "semantic_match": round(semantic_score * 100, 1),
                "skills_match": round(skill_score * 100, 1),
                "experience_match": round(exp_score * 100, 1),
                "education_match": round(edu_score * 100, 1),
                "recency_match": round(recency_score * 100, 1),
                "matched_skills": data['matching'],
                "missing_skills": missing_skills,
                "years_experience": cv_years,
                "required_experience": f"{jd_min}-{jd_max} years" if jd_max > 0 else "Not specified",
                "experience_label": exp_label,
                "education_level": edu_level,
                "recency_status": recency_label,
                "skill_details": skill_breakdown,
                "confidence_boost": round(confidence_boost * 100, 1),
                "critical_penalty": round(critical_penalty * 100, 1)
            },
            "weights_used": {k: f"{v*100:.0f}%" for k, v in weights.items()},
            "analysis": data
        }
