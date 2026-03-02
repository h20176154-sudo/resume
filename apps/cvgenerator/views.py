import os
import re
import uuid
import fitz  # PyMuPDF
from django.conf import settings
from django.http import FileResponse, HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from .models import CVGeneration
from docx import Document
from docx.shared import Pt
from docx.shared import RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import groq
import tempfile


def get_groq_client():
    """Get Groq client instance"""
    try:
        groq_client = groq.Groq(
            api_key=os.environ.get('GROQ_API_KEY')
        )
        return groq_client
    except Exception as e:
        print(f"Error initializing Groq client: {e}")
        return None


def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""


def create_word_document(text, filename):
    """Create a Word document from markdown text with ATS-friendly formatting"""
    doc = Document()
    
    # Configure margins (1 inch = 914400 twips)
    sections = doc.sections
    for section in sections:
        section.top_margin = Pt(72)  # 1 inch
        section.bottom_margin = Pt(72)
        section.left_margin = Pt(72)
        section.right_margin = Pt(72)
    
    # Parse the content
    lines = text.split('\n')
    current_section = None
    in_table = False
    table_data = []
    
    for line in lines:
        line = line.strip()
        if not line:
            # Add spacing
            doc.add_paragraph()
            continue
        
        # Handle section headers (##)
        if line.startswith('##'):
            title = line.lstrip('#').strip()
            heading = doc.add_heading(title, level=2)
            heading.alignment = WD_ALIGN_PARAGRAPH.LEFT
            
            # Format heading
            for run in heading.runs:
                run.font.size = Pt(14)
                run.font.bold = True
                run.font.color.rgb = RGBColor(102, 126, 234)
            continue
        
        # Handle sub-headers (###)
        if line.startswith('###'):
            title = line.lstrip('#').strip()
            heading = doc.add_heading(title, level=3)
            for run in heading.runs:
                run.font.size = Pt(12)
                run.font.bold = True
            continue
        
        # Handle tables
        if '|' in line and line.count('|') >= 2:
            # Skip separator lines
            if re.match(r'^[\|\s:\-]+$', line):
                continue
            
            cells = [c.strip() for c in line.split('|')]
            cells = [c for c in cells if c]  # Remove empty cells
            
            if cells:
                if not in_table:
                    # Start a new table
                    table = doc.add_table(rows=1, cols=len(cells))
                    table.style = 'Light Grid Accent 1'
                    row = table.rows[0]
                    
                    # Header row
                    for i, cell_text in enumerate(cells):
                        # Remove markdown bold
                        cell_text = re.sub(r'\*\*(.+?)\*\*', r'\1', cell_text)
                        cell = row.cells[i]
                        cell.text = cell_text
                        # Make header bold
                        cell.paragraphs[0].runs[0].font.bold = True
                        cell.paragraphs[0].runs[0].font.size = Pt(11)
                    in_table = True
                else:
                    # Add data row
                    row = table.add_row()
                    for i, cell_text in enumerate(cells):
                        if i < len(cells):
                            # Remove markdown bold
                            cell_text = re.sub(r'\*\*(.+?)\*\*', r'\1', cell_text)
                            row.cells[i].text = cell_text
                            row.cells[i].paragraphs[0].runs[0].font.size = Pt(10.5)
            continue
        
        # If we were in a table and hit non-table line, exit table mode
        if in_table and '|' not in line:
            in_table = False
        
        # Handle bullet points
        if line.startswith('- ') or line.startswith('•') or line.startswith('* '):
            content = line.lstrip('-•*').strip()
            # Remove markdown formatting
            content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)
            p = doc.add_paragraph(content, style='List Bullet')
            p.paragraph_format.left_indent = Pt(18)
            p.runs[0].font.size = Pt(10.5)
            continue
        
        # Regular paragraphs
        p = doc.add_paragraph()
        
        # Handle bold text in paragraphs
        parts = re.split(r'(\*\*.+?\*\*)', line)
        for part in parts:
            run = p.add_run(part.replace('**', ''))
            run.font.size = Pt(10.5)
            if part.startswith('**') and part.endswith('**'):
                run.font.bold = True
                run.font.color.rgb = RGBColor(51, 51, 51)
    
    # Save document
    exports_dir = os.path.join(settings.MEDIA_ROOT, 'exports')
    os.makedirs(exports_dir, exist_ok=True)
    doc_path = os.path.join(exports_dir, filename)
    doc.save(doc_path)
    return doc_path


class GenerateCVView(APIView):
    """Generate AI-enhanced CV from uploaded PDF"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            # Get uploaded file and extra notes
            uploaded_file = request.FILES.get('file')
            extra_notes = request.data.get('extra', '')
            
            if not uploaded_file:
                return Response(
                    {'error': 'No file uploaded'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save uploaded file temporarily
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)
            temp_file.close()
            
            # Extract text from PDF
            original_text = extract_text_from_pdf(temp_file.name)
            
            if not original_text:
                os.unlink(temp_file.name)
                return Response(
                    {'error': 'Could not extract text from PDF'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate AI-enhanced content
            groq_client = get_groq_client()
            if not groq_client:
                os.unlink(temp_file.name)
                return Response(
                    {'error': 'AI service unavailable'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            prompt = f"""
            Expand this resume into a professionally styled **4–10 page CV**.

            Make it:
            ✅ ATS-friendly
            ✅ Rich in storytelling
            ✅ Highly detailed bullet points
            ✅ Strong technical impact
            ✅ Leadership-focused
            ✅ Quantified achievements
            ✅ Expanded responsibilities
            ✅ Domain-keywords included
            ✅ Professional tone

            Include structured sections:
            - Executive Summary
            - Key Skills & Competencies
            - Technical Proficiencies (multilevel)
            - Professional Experience (detailed + achievements)
            - Academic Research
            - Major Projects (expanded)
            - Leadership Experience
            - Awards & Recognition
            - Certifications
            - Community Contributions
            - Soft Skills
            - Publications / Talks
            - Languages
            - Interests

            Add value and depth. Produce long output.

            Resume Source:
            {original_text}
            
            Additional information to include:
            {extra_notes}
            
            Generate a comprehensive, professional CV in markdown format with extensive detail and multiple pages of content.
            """
            
            try:
                response = groq_client.chat.completions.create(
                        model="openai/gpt-oss-20b", 
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=8000
                )
                generated_content = response.choices[0].message.content
            except Exception as e:
                print(f"Groq API error: {e}")
                os.unlink(temp_file.name)
                return Response(
                    {'error': 'Failed to generate AI content'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Create Word document
            filename = f"cv_{request.user.id if request.user.is_authenticated else 'anonymous'}_{uuid.uuid4().hex[:8]}.docx"
            word_file_path = create_word_document(generated_content, filename)
            
            # Clean up temp file
            os.unlink(temp_file.name)
            
            # Save to database if user is authenticated
            if request.user.is_authenticated:
                cv_generation = CVGeneration.objects.create(
                    user=request.user,
                    original_text=original_text,
                    extra_notes=extra_notes,
                    generated_content=generated_content,
                    word_file_path=word_file_path
                )
            
            return Response({
                'original': original_text,
                'generated': generated_content,
                'word_file': word_file_path,
                'success': True
            })
            
        except Exception as e:
            print(f"Error in GenerateCVView: {e}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExportWordView(APIView):
    """Export generated Word document"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            file_path = request.GET.get('file')
            if not file_path:
                return Response(
                    {'error': 'No file specified'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if file exists
            if not os.path.exists(file_path):
                return Response(
                    {'error': 'File not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Return file as download
            response = FileResponse(
                open(file_path, 'rb'),
                as_attachment=True,
                filename=os.path.basename(file_path)
            )
            response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            return response
            
        except Exception as e:
            print(f"Error in ExportWordView: {e}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
