from pydantic import BaseModel, Field

from tools.base import Tool, ToolInvocation, ToolKind, ToolResults
from utils.path import is_binary_file, resolve_path
from utils.text import count_tokens, truncate_text


class ReadFileParams(BaseModel):
    path: str = Field(..., description="Path of file to read")
    offset: int = Field(
        1,
        ge=0,
        description="Line number from where to start reading file 1 based index",
    )

    limit: int | None = Field(
        None,
        description="Number of lines to read from file starting from offset, if not provided reads till end of file",
    )


class ReadFileTool(Tool):
    name = "read_file"
    description = "Read the file content from given path and return contect from starting line to offset provided.If limit is not provided read till end of file.Cannot be used to read binary files."
    kind = ToolKind.READ
    schema = ReadFileParams

    MAX_SIZE = 1204 * 1024 * 10
    MAX_OUTPUT_TOKEN = 25000

    async def execute(self, invocation: ToolInvocation) -> ToolResults:
        params = ReadFileParams(**invocation.parameters)
        path = resolve_path(invocation.cwd, params.path)

        if not path.exists():
            return ToolResults.error_result(f"File Not Found {path}")
        if not path.is_file():
            return ToolResults.error_result(f"Path is not a file {path}")
        size = path.stat().st_size
        if size > self.MAX_SIZE:
            return ToolResults.error_result(
                f"File size too large {size / 1024 / 1024:.2f}MB"
                f"Max allowed size is {self.MAX_SIZE / 1024 / 1024}MB"
            )
        if is_binary_file(path):
            size_st = f"{size / 1024 / 1024:.2f}MB "
            return ToolResults.error_result(
                f"Cannot Read Binary Files {path.name} {size_st}"
                f"This Tool only reads text file"
            )
        try:
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = path.read_text(encoding="latin-1")

            lines = content.splitlines()
            total_lines = len(lines)
            if total_lines == 0:
                return ToolResults.success_result(
                    "File is empty", truncated=False, metadata={"lines": 0}
                )
            start_idx = max(0, params.offset - 1)

            if params.limit:
                end_idx = min(start_idx + params.limit, total_lines)
            else:
                end_idx = total_lines

            selected_lines = lines[start_idx:end_idx]
            formatted_lines = []
            for i, line in enumerate(selected_lines, start=start_idx + 1):
                formatted_lines.append(f"{i:6}:{line}")
            output = "\n".join(formatted_lines)

            token_count = count_tokens(
                output, "mistralai/mistral-small-3.1-24b-instruct:free"
            )
            truncated = False
            if token_count > self.MAX_OUTPUT_TOKEN:
                output = truncate_text(
                    output,
                    self.MAX_OUTPUT_TOKEN,
                    suffix=f"\n...[truncated,{total_lines} total lines]",
                )
                truncated = True
            metadata_lines = []
            if start_idx > 0 or end_idx < total_lines:
                metadata_lines.append(
                    f"showing lines {start_idx + 1} to {end_idx} of {total_lines}"
                )
            if metadata_lines:
                header = "|".join(metadata_lines) + "\n\n"
                output = header + output

            return ToolResults.success_result(
                output=output,
                truncated=truncated,
                metadata={
                    "path": str(path),
                    "total_lines": total_lines,
                    "start_line": start_idx + 1,
                    "end_line": end_idx,
                },
            )
        except Exception as e:
            return ToolResults.error_result(f"Error reading file:{str(e)}")
