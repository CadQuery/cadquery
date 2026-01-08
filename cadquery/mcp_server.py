# Copyright (c) CadQuery Development Team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
CadQuery MCP (Model Context Protocol) Server.

This module provides an MCP server that allows AI assistants like Claude
to execute CadQuery scripts and receive rendered images of 3D models.

Usage:
    Run as a standalone server:
        python -m cadquery.mcp_server

    Or use the entry point:
        cadquery-mcp

Configuration in Claude Code (~/.claude/settings.json):
    {
        "mcpServers": {
            "cadquery": {
                "command": "cadquery-mcp"
            }
        }
    }
"""

import asyncio
import base64
import tempfile
import traceback
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent

from . import cqgi
from .vis import show


server = Server("cadquery")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available CadQuery tools."""
    return [
        Tool(
            name="render",
            description=(
                "Execute CadQuery Python code and return a rendered image of the 3D model. "
                "The code should use show_object() to output shapes, or assign the final result to 'result'. "
                "Example: result = cq.Workplane('XY').box(1, 2, 3). "
                "Returns SVG by default (works headlessly), or PNG if format='png' and display is available."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "CadQuery Python code to execute",
                    },
                    "format": {
                        "type": "string",
                        "description": "Output format: 'svg' (default, headless) or 'png' (requires display)",
                        "enum": ["svg", "png"],
                        "default": "svg",
                    },
                    "width": {
                        "type": "integer",
                        "description": "Image width in pixels (default: 800, PNG only)",
                        "default": 800,
                    },
                    "height": {
                        "type": "integer",
                        "description": "Image height in pixels (default: 600, PNG only)",
                        "default": 600,
                    },
                },
                "required": ["code"],
            },
        ),
        Tool(
            name="inspect",
            description=(
                "Execute CadQuery code and return geometry information about the resulting shape, "
                "including bounding box dimensions, volume, surface area, and center of mass."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "CadQuery Python code to execute",
                    },
                },
                "required": ["code"],
            },
        ),
        Tool(
            name="get_parameters",
            description=(
                "Parse CadQuery code and extract the parameters (variables) that can be customized. "
                "Returns parameter names, types, and default values."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "CadQuery Python code to parse",
                    },
                },
                "required": ["code"],
            },
        ),
        Tool(
            name="export",
            description=(
                "Execute CadQuery code and export the result to a file. "
                "Supported formats: STEP, STL, SVG, DXF, AMF, 3MF, VRML, BREP."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "CadQuery Python code to execute",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Output filename (format determined by extension)",
                    },
                    "format": {
                        "type": "string",
                        "description": "Export format (optional, inferred from filename if not provided)",
                        "enum": ["STEP", "STL", "SVG", "DXF", "AMF", "3MF", "VRML", "BREP"],
                    },
                },
                "required": ["code", "filename"],
            },
        ),
    ]


def _extract_shape(build_result, env):
    """Extract the shape from a build result or environment."""
    # First try to get from show_object() calls
    if build_result.first_result is not None:
        return build_result.first_result.shape

    # Fall back to 'result' variable in environment
    if "result" in env:
        return env["result"]

    return None


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent | ImageContent]:
    """Handle tool calls."""

    if name == "render":
        return await _handle_render(arguments)
    elif name == "inspect":
        return await _handle_inspect(arguments)
    elif name == "get_parameters":
        return await _handle_get_parameters(arguments)
    elif name == "export":
        return await _handle_export(arguments)
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def _handle_render(arguments: dict[str, Any]) -> list[TextContent | ImageContent]:
    """Execute CadQuery code and return a rendered image (SVG or PNG)."""
    code = arguments["code"]
    output_format = arguments.get("format", "svg")
    width = arguments.get("width", 800)
    height = arguments.get("height", 600)

    try:
        # Parse and execute the script using CQGI
        model = cqgi.parse(code)
        result = model.build()

        if result.exception:
            return [TextContent(
                type="text",
                text=f"Execution error:\n{traceback.format_exception(type(result.exception), result.exception, result.exception.__traceback__)}"
            )]

        shape = _extract_shape(result, result.env)

        if shape is None:
            return [TextContent(
                type="text",
                text="No shape produced. Use show_object(shape) or assign to 'result' variable."
            )]

        # Get the underlying Shape object if it's a Workplane
        if hasattr(shape, "val"):
            shape = shape.val()

        if output_format == "svg":
            # SVG rendering (works headlessly, no display required)
            from .occ_impl.exporters.svg import getSVG

            svg_content = getSVG(shape, opts={"width": width, "height": height})
            svg_data = base64.standard_b64encode(svg_content.encode("utf-8")).decode("utf-8")

            return [ImageContent(type="image", data=svg_data, mimeType="image/svg+xml")]

        else:
            # PNG rendering using VTK (requires display/OpenGL)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                screenshot_path = f.name

            # Use vis.show() with screenshot parameter
            show(
                shape,
                screenshot=screenshot_path,
                interact=False,
                width=width,
                height=height,
            )

            # Read and encode the image
            with open(screenshot_path, "rb") as img_file:
                img_data = base64.standard_b64encode(img_file.read()).decode("utf-8")

            return [ImageContent(type="image", data=img_data, mimeType="image/png")]

    except SyntaxError as e:
        return [TextContent(type="text", text=f"Syntax error: {e}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {type(e).__name__}: {e}")]


async def _handle_inspect(arguments: dict[str, Any]) -> list[TextContent | ImageContent]:
    """Execute CadQuery code and return geometry information."""
    code = arguments["code"]

    try:
        model = cqgi.parse(code)
        result = model.build()

        if result.exception:
            return [TextContent(
                type="text",
                text=f"Execution error: {result.exception}"
            )]

        shape = _extract_shape(result, result.env)

        if shape is None:
            return [TextContent(
                type="text",
                text="No shape produced. Use show_object(shape) or assign to 'result' variable."
            )]

        # Get the underlying Shape object if it's a Workplane
        if hasattr(shape, "val"):
            shape = shape.val()

        # Gather geometry information
        bb = shape.BoundingBox()
        info_lines = [
            "Geometry Information:",
            f"  Bounding Box:",
            f"    X: {bb.xmin:.4f} to {bb.xmax:.4f} (size: {bb.xlen:.4f})",
            f"    Y: {bb.ymin:.4f} to {bb.ymax:.4f} (size: {bb.ylen:.4f})",
            f"    Z: {bb.zmin:.4f} to {bb.zmax:.4f} (size: {bb.zlen:.4f})",
        ]

        # Try to get volume (only works for solids)
        try:
            volume = shape.Volume()
            info_lines.append(f"  Volume: {volume:.4f}")
        except Exception:
            pass

        # Try to get surface area
        try:
            area = shape.Area()
            info_lines.append(f"  Surface Area: {area:.4f}")
        except Exception:
            pass

        # Try to get center of mass
        try:
            com = shape.Center()
            info_lines.append(f"  Center of Mass: ({com.x:.4f}, {com.y:.4f}, {com.z:.4f})")
        except Exception:
            pass

        # Count topological entities
        try:
            info_lines.append(f"  Topology:")
            info_lines.append(f"    Solids: {len(shape.Solids())}")
            info_lines.append(f"    Faces: {len(shape.Faces())}")
            info_lines.append(f"    Edges: {len(shape.Edges())}")
            info_lines.append(f"    Vertices: {len(shape.Vertices())}")
        except Exception:
            pass

        info_lines.append(f"  Build Time: {result.buildTime:.4f}s")

        return [TextContent(type="text", text="\n".join(info_lines))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {type(e).__name__}: {e}")]


async def _handle_get_parameters(arguments: dict[str, Any]) -> list[TextContent | ImageContent]:
    """Parse CadQuery code and extract parameters."""
    code = arguments["code"]

    try:
        model = cqgi.parse(code)
        params = model.metadata.parameters

        if not params:
            return [TextContent(type="text", text="No parameters found in the script.")]

        lines = ["Parameters found:"]
        for name, param in params.items():
            type_name = param.varType.__name__ if param.varType else "unknown"
            lines.append(f"  {name}: {type_name} = {param.default_value}")
            if param.desc:
                lines.append(f"    Description: {param.desc}")
            if param.valid_values:
                lines.append(f"    Valid values: {param.valid_values}")

        return [TextContent(type="text", text="\n".join(lines))]

    except SyntaxError as e:
        return [TextContent(type="text", text=f"Syntax error: {e}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {type(e).__name__}: {e}")]


async def _handle_export(arguments: dict[str, Any]) -> list[TextContent | ImageContent]:
    """Execute CadQuery code and export to file."""
    code = arguments["code"]
    filename = arguments["filename"]
    export_format = arguments.get("format")

    try:
        model = cqgi.parse(code)
        result = model.build()

        if result.exception:
            return [TextContent(
                type="text",
                text=f"Execution error: {result.exception}"
            )]

        shape = _extract_shape(result, result.env)

        if shape is None:
            return [TextContent(
                type="text",
                text="No shape produced. Use show_object(shape) or assign to 'result' variable."
            )]

        # Import exporters
        from .occ_impl.exporters import export

        # Get the underlying Shape if it's a Workplane
        if hasattr(shape, "val"):
            shape = shape.val()

        # Export
        export(shape, filename, exportType=export_format)

        return [TextContent(type="text", text=f"Exported to: {filename}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {type(e).__name__}: {e}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def run():
    """Entry point for the cadquery-mcp command."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
