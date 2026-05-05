from pydantic import BaseModel, ConfigDict, Field


class AddTaskArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(
        ..., description="Original task text from the user without changes."
    )


class AddNoteArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(
        ...,
        description=(
            "Short title for filename (3-4 words). No timestamp, no extension."
        ),
    )
    content: str = Field(
        ..., description="Original note text from the user without changes."
    )


class GetHabrArticlesArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": (
                "Create a Todoist task from the original user text. Use for tasks."
            ),
            "parameters": AddTaskArgs.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_note",
            "description": (
                "Create a GitHub note from the original user text. Use for ideas/notes."
            ),
            "parameters": AddNoteArgs.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_habr_articles",
            "description": "Fetch top 5 recent Habr articles from predefined hubs.",
            "parameters": GetHabrArticlesArgs.model_json_schema(),
        },
    },
]
