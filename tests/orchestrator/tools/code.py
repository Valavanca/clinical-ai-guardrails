from __future__ import annotations

from pathlib import Path
from typing import Union
import json

from smolagents import Tool


import nbformat
from nbconvert import MarkdownExporter
from pathlib import Path
from dataclasses import dataclass

@dataclass
class NotebookView:
    """Notebook representation"""
    path: str
    markdown_content: str
    cell_count: int
    code_cells: int
    executed_cells: int
    
    @property
    def execution_rate(self) -> float:
        return (self.executed_cells / self.code_cells * 100) if self.code_cells else 0
    
    @property
    def summary(self) -> str:
        name = Path(self.path).name
        return f"{name}: {self.cell_count} cells ({self.code_cells} code, {self.execution_rate:.0f}% executed)"

class ReadIPYNBTool(Tool):
    name = "read_ipynb"
    description = """Load a Jupyter notebook (.ipynb) from disk and return its contents as a markdown string."""
    inputs = {
        "notebook_path": {
            "type": "string",
            "description": "Filesystem path to the notebook.",
        }
    }
    output_type = "string"

    def forward(self, notebook_path: Union[str, Path],
    ) -> str:
        """Read a Jupyter notebook
        
        Args:
            notebook_path: Filesystem path to the notebook.

        Returns:
            Notebook content as a markdown string with metadata.
        """
        path = Path(notebook_path).expanduser().resolve()
        if path.suffix.lower() != ".ipynb":
            raise ValueError("Supplied file must have a .ipynb extension")
        with open(path) as f:
            nb = nbformat.read(f, as_version=4)

        exporter = MarkdownExporter()
        markdown_content, _ = exporter.from_notebook_node(nb)
        
        cells = nb.cells
        code_cells = [c for c in cells if c.cell_type == 'code']
        executed_cells = [c for c in code_cells if c.execution_count is not None]
        
        notebook = NotebookView(
            path=str(path),
            markdown_content=markdown_content,
            cell_count=len(cells),
            code_cells=len(code_cells),
            executed_cells=len(executed_cells)
        )
    
        response = f"{notebook.summary}\n\n{notebook.markdown_content}"
        return response