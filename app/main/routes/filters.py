from bs4 import BeautifulSoup

def remove_headings_filter(html_content):
    """Remove heading tags (h1-h6) from HTML content while preserving other formatting"""
    if not html_content:
        return html_content
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove all heading tags (h1, h2, h3, h4, h5, h6)
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        heading.decompose()
    
    return str(soup)