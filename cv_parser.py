
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
        
    # 4. Name Extraction (Heuristic: First significant line)
    try:
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if lines:
            # Simple heuristic: first line is usually the name
            # Filtering out common header words if they appear alone
            potential_name = lines[0]
            if len(potential_name.split()) < 5 and "resume" not in potential_name.lower() and "curriculum" not in potential_name.lower():
                 info['name'] = potential_name
            elif len(lines) > 1:
                 # Try second line if first is likely a header
                 info['name'] = lines[1]
    except Exception:
        pass

    return info
