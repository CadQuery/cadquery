"""
Tests for the MCP (Model Context Protocol) server functionality.

These tests verify that:
- The MCP server can execute CadQuery scripts
- SVG rendering works correctly (headless)
- Geometry inspection returns correct values
- Parameter extraction works
- Export functionality works
- Error handling is correct

Note: These tests require the 'mcp' package to be installed.
They will be skipped if mcp is not available (e.g., in conda CI environments).
"""

import pytest
import asyncio
import base64
import tempfile
import os
from tests import BaseTest

# Skip all tests in this module if mcp is not installed
mcp = pytest.importorskip("mcp", reason="MCP package not installed")


class TestMCPServer(BaseTest):
    """Test cases for the CadQuery MCP server."""

    def test_import(self):
        """Test that the MCP server module can be imported."""
        from cadquery import mcp_server
        self.assertIsNotNone(mcp_server.server)

    def test_list_tools(self):
        """Test that list_tools returns the expected tools."""
        from cadquery.mcp_server import list_tools

        tools = asyncio.run(list_tools())
        tool_names = [t.name for t in tools]

        self.assertIn("render", tool_names)
        self.assertIn("inspect", tool_names)
        self.assertIn("get_parameters", tool_names)
        self.assertIn("export", tool_names)

    def test_render_svg_simple_box(self):
        """Test SVG rendering of a simple box."""
        from cadquery.mcp_server import _handle_render

        result = asyncio.run(_handle_render({
            "code": "import cadquery as cq\nresult = cq.Workplane('XY').box(10, 20, 30)",
            "format": "svg",
        }))

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].type, "image")
        self.assertEqual(result[0].mimeType, "image/svg+xml")

        # Decode and verify SVG content
        svg_content = base64.b64decode(result[0].data).decode("utf-8")
        self.assertIn("<svg", svg_content)
        self.assertIn("</svg>", svg_content)
        self.assertIn("<path", svg_content)  # Should have path elements for the box edges

    def test_render_svg_with_show_object(self):
        """Test SVG rendering using show_object() instead of result variable."""
        from cadquery.mcp_server import _handle_render

        code = """
import cadquery as cq
box = cq.Workplane('XY').box(5, 5, 5)
show_object(box)
"""
        result = asyncio.run(_handle_render({"code": code, "format": "svg"}))

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].type, "image")
        self.assertEqual(result[0].mimeType, "image/svg+xml")

    def test_render_no_shape_error(self):
        """Test that render returns an error when no shape is produced."""
        from cadquery.mcp_server import _handle_render

        result = asyncio.run(_handle_render({
            "code": "x = 1 + 1",  # No shape produced
            "format": "svg",
        }))

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].type, "text")
        self.assertIn("No shape produced", result[0].text)

    def test_render_syntax_error(self):
        """Test that render handles syntax errors gracefully."""
        from cadquery.mcp_server import _handle_render

        result = asyncio.run(_handle_render({
            "code": "this is not valid python!!!",
            "format": "svg",
        }))

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].type, "text")
        self.assertIn("Syntax error", result[0].text)

    def test_render_execution_error(self):
        """Test that render handles execution errors gracefully."""
        from cadquery.mcp_server import _handle_render

        result = asyncio.run(_handle_render({
            "code": "raise ValueError('test error')",
            "format": "svg",
        }))

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].type, "text")
        self.assertIn("Execution error", result[0].text)

    def test_inspect_box_geometry(self):
        """Test geometry inspection of a simple box."""
        from cadquery.mcp_server import _handle_inspect

        result = asyncio.run(_handle_inspect({
            "code": "import cadquery as cq\nresult = cq.Workplane('XY').box(10, 20, 30)",
        }))

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].type, "text")

        text = result[0].text
        self.assertIn("Bounding Box", text)
        self.assertIn("10.0000", text)  # X size
        self.assertIn("20.0000", text)  # Y size
        self.assertIn("30.0000", text)  # Z size
        self.assertIn("Volume", text)
        self.assertIn("6000", text)  # Volume = 10 * 20 * 30

    def test_inspect_topology(self):
        """Test that topology information is returned."""
        from cadquery.mcp_server import _handle_inspect

        result = asyncio.run(_handle_inspect({
            "code": "import cadquery as cq\nresult = cq.Workplane('XY').box(1, 1, 1)",
        }))

        text = result[0].text
        self.assertIn("Topology", text)
        self.assertIn("Solids: 1", text)
        self.assertIn("Faces: 6", text)  # A box has 6 faces
        self.assertIn("Edges: 12", text)  # A box has 12 edges
        self.assertIn("Vertices: 8", text)  # A box has 8 vertices

    def test_get_parameters_finds_variables(self):
        """Test that get_parameters extracts script parameters."""
        from cadquery.mcp_server import _handle_get_parameters

        code = """
height = 10.0
width = 20.0
name = "test"
enabled = True

import cadquery as cq
result = cq.Workplane('XY').box(width, height, 5)
"""
        result = asyncio.run(_handle_get_parameters({"code": code}))

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].type, "text")

        text = result[0].text
        self.assertIn("height", text)
        self.assertIn("width", text)
        self.assertIn("name", text)
        self.assertIn("enabled", text)
        self.assertIn("10.0", text)
        self.assertIn("20.0", text)

    def test_get_parameters_no_params(self):
        """Test get_parameters when no parameters are found."""
        from cadquery.mcp_server import _handle_get_parameters

        result = asyncio.run(_handle_get_parameters({
            "code": "import cadquery as cq\nresult = cq.Workplane('XY').box(1, 2, 3)",
        }))

        self.assertEqual(len(result), 1)
        self.assertIn("No parameters found", result[0].text)

    def test_export_step(self):
        """Test STEP export functionality."""
        from cadquery.mcp_server import _handle_export

        with tempfile.NamedTemporaryFile(suffix=".step", delete=False) as f:
            filename = f.name

        try:
            result = asyncio.run(_handle_export({
                "code": "import cadquery as cq\nresult = cq.Workplane('XY').box(10, 10, 10)",
                "filename": filename,
            }))

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].type, "text")
            self.assertIn("Exported to", result[0].text)

            # Verify file was created and has content
            self.assertTrue(os.path.exists(filename))
            self.assertGreater(os.path.getsize(filename), 0)
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_export_stl(self):
        """Test STL export functionality."""
        from cadquery.mcp_server import _handle_export

        with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as f:
            filename = f.name

        try:
            result = asyncio.run(_handle_export({
                "code": "import cadquery as cq\nresult = cq.Workplane('XY').box(5, 5, 5)",
                "filename": filename,
            }))

            self.assertEqual(len(result), 1)
            self.assertIn("Exported to", result[0].text)
            self.assertTrue(os.path.exists(filename))
            self.assertGreater(os.path.getsize(filename), 0)
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_export_no_shape_error(self):
        """Test that export returns an error when no shape is produced."""
        from cadquery.mcp_server import _handle_export

        with tempfile.NamedTemporaryFile(suffix=".step", delete=False) as f:
            filename = f.name

        try:
            result = asyncio.run(_handle_export({
                "code": "x = 1",
                "filename": filename,
            }))

            self.assertEqual(len(result), 1)
            self.assertIn("No shape produced", result[0].text)
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_call_tool_dispatch(self):
        """Test that call_tool correctly dispatches to handlers."""
        from cadquery.mcp_server import call_tool

        # Test render dispatch
        result = asyncio.run(call_tool("render", {
            "code": "import cadquery as cq\nresult = cq.Workplane('XY').box(1, 1, 1)",
            "format": "svg",
        }))
        self.assertEqual(result[0].type, "image")

        # Test inspect dispatch
        result = asyncio.run(call_tool("inspect", {
            "code": "import cadquery as cq\nresult = cq.Workplane('XY').box(1, 1, 1)",
        }))
        self.assertIn("Bounding Box", result[0].text)

        # Test unknown tool
        result = asyncio.run(call_tool("unknown_tool", {}))
        self.assertIn("Unknown tool", result[0].text)

    def test_complex_model_render(self):
        """Test rendering a more complex model."""
        from cadquery.mcp_server import _handle_render

        code = """
import cadquery as cq

# Create a box with a hole
result = (
    cq.Workplane('XY')
    .box(20, 20, 10)
    .faces('>Z')
    .workplane()
    .hole(5)
)
"""
        result = asyncio.run(_handle_render({"code": code, "format": "svg"}))

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].type, "image")

        svg_content = base64.b64decode(result[0].data).decode("utf-8")
        self.assertIn("<svg", svg_content)

    def test_render_with_dimensions(self):
        """Test that width/height parameters are accepted."""
        from cadquery.mcp_server import _handle_render

        result = asyncio.run(_handle_render({
            "code": "import cadquery as cq\nresult = cq.Workplane('XY').box(1, 1, 1)",
            "format": "svg",
            "width": 400,
            "height": 300,
        }))

        self.assertEqual(result[0].type, "image")
        # SVG should be generated successfully
        svg_content = base64.b64decode(result[0].data).decode("utf-8")
        self.assertIn("<svg", svg_content)


class TestMCPServerEdgeCases(BaseTest):
    """Test edge cases and error handling."""

    def test_empty_code(self):
        """Test handling of empty code."""
        from cadquery.mcp_server import _handle_render

        result = asyncio.run(_handle_render({"code": "", "format": "svg"}))
        self.assertEqual(result[0].type, "text")
        self.assertIn("No shape produced", result[0].text)

    def test_whitespace_only_code(self):
        """Test handling of whitespace-only code."""
        from cadquery.mcp_server import _handle_render

        result = asyncio.run(_handle_render({"code": "   \n\n   ", "format": "svg"}))
        self.assertEqual(result[0].type, "text")
        self.assertIn("No shape produced", result[0].text)

    def test_inspect_with_show_object(self):
        """Test inspect works with show_object() syntax."""
        from cadquery.mcp_server import _handle_inspect

        code = """
import cadquery as cq
box = cq.Workplane('XY').box(5, 10, 15)
show_object(box)
"""
        result = asyncio.run(_handle_inspect({"code": code}))

        text = result[0].text
        self.assertIn("5.0000", text)
        self.assertIn("10.0000", text)
        self.assertIn("15.0000", text)
