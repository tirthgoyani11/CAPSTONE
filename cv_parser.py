
import pdfplumber
import docx
import re
import os

def extract_text(filepath):
    """
    Extracts text from a file (PDF, DOCX, or TXT).
    """
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == '.pdf':
        return extract_text_from_pdf(filepath)
    elif ext == '.docx':
        return extract_text_from_docx(filepath)
    elif ext == '.txt':
        return extract_text_from_txt(filepath)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

def extract_text_from_pdf(filepath):
    text = ""
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            data = page.extract_text()
            if data:
                text += data + "\n"
    return text

def extract_text_from_docx(filepath):
    doc = docx.Document(filepath)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_txt(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def parse_cv_sections(text):
    """
    A heuristic-based parser to try and separate CV into sections.
    This is not perfect but improves scoring granularly.
    """
    sections = {
        'experience': '',
        'education': '',
        'skills': '',
        'other': ''
    }
    
    # Simple keyword based splitting (can be improved with NER later)
    # Using lowercase for matching
    lower_text = text.lower()
    
    # basic indices
    idx_exp = max(lower_text.find('experience'), lower_text.find('work history'), lower_text.find('employment'))
    idx_edu = max(lower_text.find('education'), lower_text.find('academic'), lower_text.find('qualifications'))
    idx_skills = max(lower_text.find('skills'), lower_text.find('technologies'), lower_text.find('competencies'))
    
    # Sort indices to know order
    indices = sorted([(idx_exp, 'experience'), (idx_edu, 'education'), (idx_skills, 'skills')])
    indices = [i for i in indices if i[0] != -1]
    
    if not indices:
        return {'other': text} # Return full text if no sections found

    # Slice text
    # Assuming 'other' (header info) is before the first section
    sections['other'] = text[:indices[0][0]]
    
    for i in range(len(indices)):
        start_idx = indices[i][0]
        section_name = indices[i][1]
        
        if i < len(indices) - 1:
            end_idx = indices[i+1][0]
            sections[section_name] = text[start_idx:end_idx]
        else:
            sections[section_name] = text[start_idx:]
            
    return sections

def extract_candidate_info(text):
    """
    Extracts structured information like Email, Phone, and Education.
    """
    info = {
        'email': None,
        'phone': None,
        'education': [],
        'name': None
    }
    
    if not text:
        return info
    
    # 1. Email Extraction
    try:
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_match = re.search(email_pattern, text)
        if email_match:
            info['email'] = email_match.group(0)
    except Exception:
        pass
        
    # 2. Phone Extraction
    # Use re.search for the first valid occurrence of a phone-like pattern
    try:
        # Regex for standard formats: (123) 456-7890, 123-456-7890, +1 123 456 7890
        phone_pattern = r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            info['phone'] = phone_match.group(0).strip()
    except Exception:
        pass

    # 3. Education Extraction
    try:
        degrees = [
            'B.Tech', 'B.E.', 'B.Sc', 'BCA', 'B.A.',
            'M.Tech', 'M.E.', 'M.Sc', 'MCA', 'M.B.A.', 'MBA', 'M.A.',
            'Ph.D', 'Doctorate', 'Bachelor', 'Master', 'Diploma'
        ]
        
        found_degrees = set()
        lower_text = text.lower()
        for degree in degrees:
            # Word boundary check
            if re.search(r'\b' + re.escape(degree.lower()) + r'\b', lower_text):
                found_degrees.add(degree)
        
        if found_degrees:
            info['education'] = list(found_degrees)
    except Exception:
        pass
        
    # 4. Name Extraction (Improved Heuristic)
    try:
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if lines:
            # Iterate first few lines to find a name-like string (2-3 words, no numbers)
            for i in range(min(10, len(lines))):
                candidate_line = lines[i].strip()
                # Clean up generic headers
                if any(x in candidate_line.lower() for x in ['resume', 'curriculum', 'vitae', 'cv', 'profile', 'format', 'first name', 'introduction', 'name:', 'candidate', 'contact', 'email', 'phone']):
                    continue
                # Check if it looks like a name (no digits, 2-4 words, Title Case)
                words = candidate_line.split()
                if 2 <= len(words) <= 4 and not any(char.isdigit() for char in candidate_line):
                    # Check if at least the first letter is uppercase (Title Case check)
                    if candidate_line[0].isupper(): 
                        info['name'] = candidate_line
                        break
    except Exception:
        pass

    # 5. Certifications (Stub/Heuristic)
    info['certifications'] = []
    try:
        cert_keywords = ['aws certified', 'azure', 'google cloud professional', 'pmp', 'scrum master', 'cisco', 'comptia']
        lower_text = text.lower()
        for ck in cert_keywords:
            if ck in lower_text:
                # Find the full line or context
                # simplified: just add the keyword found
                info['certifications'].append(ck.title())
    except Exception:
        pass

    return info
