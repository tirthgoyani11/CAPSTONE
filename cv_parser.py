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

def anonymize_cv(text):
    """
    Removes emails and phone numbers for blind screening.
    """
    # Remove email
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL_REDACTED]', text)
    # Remove phone (simple regex, can be improved)
    text = re.sub(r'(\+\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}', '[PHONE_REDACTED]', text)
    return text
