"""
PDF Export Tool for Research Reports.

Converts markdown reports to PDF and saves them to the output directory.
"""

import os
import re
import logging
from pathlib import Path
from typing import Optional

try:
    import markdown
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
except Exception:
    # Catch any error from WeasyPrint import (ImportError, OSError from missing native libs, etc.)
    markdown = None
    HTML = None
    CSS = None
    FontConfiguration = None


logger = logging.getLogger(__name__)


class PDFExporter:
    """
    Tool for exporting markdown reports to PDF format.
    
    Uses markdown + weasyprint to convert markdown to PDF.
    """

    def __init__(self, output_dir: str = "output") -> None:
        """
        Initialize the PDF exporter.
        
        Args:
            output_dir: Directory where PDF files will be saved
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if markdown is None or HTML is None:
            logger.warning(
                "PDFExporter: markdown or weasyprint not installed. "
                "Install with: pip install markdown weasyprint"
            )

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a string to be used as a filename.
        
        Removes or replaces invalid characters for filenames.
        """
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove leading/trailing spaces and dots
        filename = filename.strip(' .')
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
        # If empty after sanitization, use default
        if not filename:
            filename = "research_report"
        return filename

    def markdown_to_html(self, markdown_content: str) -> str:
        """
        Convert markdown content to HTML.
        
        Args:
            markdown_content: Markdown formatted text
            
        Returns:
            HTML string
        """
        if markdown is None:
            raise ImportError("markdown library is not installed. Install with: pip install markdown")
        
        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=['extra', 'codehilite', 'tables']
        )
        
        # Wrap in a styled HTML document
        html_document = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Georgia', 'Times New Roman', serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 5px;
        }}
        h3 {{
            color: #555;
            margin-top: 20px;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        ul, ol {{
            margin-left: 20px;
        }}
        blockquote {{
            border-left: 4px solid #3498db;
            margin-left: 0;
            padding-left: 20px;
            color: #666;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""
        
        return html_document

    def export_to_pdf(
        self,
        markdown_content: str,
        user_query: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Export a markdown report to PDF.
        
        Args:
            markdown_content: Markdown formatted report
            user_query: Original user query (used for filename if filename not provided)
            filename: Optional custom filename (without .pdf extension)
            
        Returns:
            Path to the saved PDF file
            
        Raises:
            ImportError: If required libraries are not installed
            Exception: If PDF generation fails
        """
        if HTML is None or CSS is None:
            raise ImportError(
                "weasyprint library is not installed. Install with: pip install weasyprint"
            )
        
        # Determine filename
        if filename is None:
            filename = self.sanitize_filename(user_query)
        else:
            filename = self.sanitize_filename(filename)
        
        # Ensure .pdf extension
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        
        pdf_path = self.output_dir / filename
        
        try:
            logger.info("PDFExporter: Converting markdown to HTML...")
            html_content = self.markdown_to_html(markdown_content)
            
            logger.info("PDFExporter: Generating PDF: %s", pdf_path)
            font_config = FontConfiguration()
            HTML(string=html_content).write_pdf(
                pdf_path,
                font_config=font_config
            )
            
            logger.info("PDFExporter: Successfully saved PDF to: %s", pdf_path)
            return str(pdf_path)
            
        except Exception as exc:
            logger.error("PDFExporter: Failed to generate PDF: %s", exc)
            raise


def export_report_to_pdf(
    markdown_content: str,
    user_query: str,
    output_dir: str = "output",
    filename: Optional[str] = None
) -> str:
    """
    Convenience function to export a markdown report to PDF.
    
    Args:
        markdown_content: Markdown formatted report
        user_query: Original user query
        output_dir: Directory where PDF will be saved
        filename: Optional custom filename (without .pdf extension)
        
    Returns:
        Path to the saved PDF file
    """
    exporter = PDFExporter(output_dir=output_dir)
    return exporter.export_to_pdf(markdown_content, user_query, filename)

