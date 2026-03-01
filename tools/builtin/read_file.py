from pydantic import BaseModel, Field

from tools.base import Tool, ToolKind


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
    kind=ToolKind.READ
    schema=ReadFileParams