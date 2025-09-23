"""
Data model used across the project.
"""

class Interaction:
    """
    Represents a single user interaction identified from the flow json file.

    Attributes:
        kind (str): The category of interaction (e.g., "click", "navigate", "typing", "scrolling", "hint").
        description (str): A human-readable description of the interaction.
        page_title (str|None): The page title where the interaction occurred, if available.
        page_url (str|None): The page URL where the interaction occurred, if available.
    """

    def __init__(self, kind, description, page_title=None, page_url=None):
        self.kind = kind
        self.description = description
        self.page_title = page_title
        self.page_url = page_url
    
    def __repr__(self):
        return (
            "Interaction(kind={!r}, description={!r}, page_title={!r}, page_url={!r})"
            .format(self.kind, self.description, self.page_title, self.page_url)
        )
