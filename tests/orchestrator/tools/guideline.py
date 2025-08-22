from pathlib import Path
from typing import Optional, Dict, List
from smolagents import Tool, tool

_CONTEXT_DIR = Path(__file__).resolve().parent.parent / "context"
_GUIDELINES_DIR = _CONTEXT_DIR / "guidelines"


def _read_text(path: Path, encoding: str = "utf-8") -> str:
    """Read a file safely and return its UTF-8 text.

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    """
    try:
        return path.read_text(encoding=encoding)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Guideline file not found at {path}. Ensure the resource is packaged "
            "or the working directory is correct."
        ) from e


class ReadMarkdownTool(Tool):
    """Enhanced tool for reading markdown files with intelligent path resolution."""
    
    name = "read_md_file"
    description = """
    Read markdown files from the clinical AI guidelines directory.
    Supports both absolute paths and relative paths within the guidelines structure.
    Can read specific guideline files by name or category.
    """
    inputs = {
        "file_path": {
            "type": "string",
            "description": "Path to markdown file. Can be absolute, relative to guidelines dir, or a known guideline name (e.g., 'statistical_validation', 'data_quality')"
        },
        "search_subdirs": {
            "type": "boolean", 
            "description": "Whether to search in subdirectories if file not found in main location",
            "default": True,
            "nullable": False
        }
    }
    output_type = "string"
    
    GUIDELINE_MAP = {
        "data_quality": "data_quality.md",
        "statistical_validation": "statistical_validation.md", 
        "model_selection": "model_selection.md",
        "clinical_integration": "clinical_integration.md",
        "sanity_checks": "sanity_checks.md",
    }
    
    def forward(self, file_path: str, search_subdirs: bool = True) -> str:
        """Read markdown file with intelligent path resolution.
        
        Args:
            file_path: Path to file or known guideline name
            search_subdirs: Whether to search subdirectories
            
        Returns:
            Contents of the markdown file as string
            
        Raises:
            FileNotFoundError: If file cannot be found
            ValueError: If file_path is invalid
        """
        
        if not file_path or not file_path.strip():
            raise ValueError("file_path cannot be empty")
        
        file_path = file_path.strip()
        
        # Check if it's a known guideline name
        if file_path in self.GUIDELINE_MAP:
            target_file = self.GUIDELINE_MAP[file_path]
            file_path = target_file
        
        # Try different path resolution strategies
        search_paths = self._get_search_paths(file_path, search_subdirs)
        
        for path in search_paths:
            if path.exists() and path.is_file():
                try:
                    content = _read_text(path)
                    # Add metadata about which file was read
                    return f"# File: {path.name}\n# Path: {path}\n\n{content}"
                except Exception as e:
                    continue  # Try next path
        
        # If we get here, file wasn't found
        searched_locations = [str(p) for p in search_paths]
        raise FileNotFoundError(
            f"Markdown file '{file_path}' not found. Searched locations:\n" + 
            "\n".join(f"  - {loc}" for loc in searched_locations)
        )
    
    def _get_search_paths(self, file_path: str, search_subdirs: bool) -> List[Path]:
        """Generate list of paths to search for the file."""
        paths = []
        path_obj = Path(file_path)
        if path_obj.is_absolute():
            paths.append(path_obj)
        paths.append(_GUIDELINES_DIR / file_path)
        paths.append(_CONTEXT_DIR / file_path)
        
        if not file_path.endswith('.md'):
            md_file = f"{file_path}.md"
            paths.append(_GUIDELINES_DIR / md_file)
            paths.append(_CONTEXT_DIR / md_file)
        
        if search_subdirs:
            for subdir in _CONTEXT_DIR.rglob('*'):
                if subdir.is_dir():
                    paths.append(subdir / file_path)
                    if not file_path.endswith('.md'):
                        paths.append(subdir / f"{file_path}.md")
        
        return paths
    
    def list_available_guidelines(self) -> Dict[str, str]:
        """List all available guideline files."""
        guidelines = {}
        
        for name, filename in self.GUIDELINE_MAP.items():
            path = _GUIDELINES_DIR / filename
            if not path.exists():
                path = _CONTEXT_DIR / filename
            
            if path.exists():
                guidelines[name] = str(path)
        
        if _GUIDELINES_DIR.exists():
            for md_file in _GUIDELINES_DIR.glob("*.md"):
                if md_file.stem not in self.GUIDELINE_MAP.values():
                    guidelines[md_file.stem] = str(md_file)
        
        return guidelines


# # Create tool instance
# read_md_file_tool = ReadMarkdownTool()


# @tool  
# def get_guideline() -> str:
#     """Return the detailed model-selection guideline as a raw Markdown string."""
#     return read_md_file_tool.forward("full_guidelines")


# @tool
# def get_decision_guideline() -> str:
#     """Return concise sanity check guidelines as a raw Markdown string.""" 
#     return read_md_file_tool.forward("sanity_checks")


# @tool
# def read_md_file(file_path: str) -> str:
#     """Read a Markdown file and return its contents as a string.
    
#     Wrapper function for ReadMarkdownTool for backward compatibility.
#     """
#     return read_md_file_tool.forward(file_path)