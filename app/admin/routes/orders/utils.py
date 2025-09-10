MAX_FILE_SIZE = 16 * 1024 * 1024  
  
def get_file_format(filename):
    """Extract file format from filename"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''