
class OntoEntity:

    uri: str
    label: str 
    comment: str
    is_literal: bool
    is_blank: bool

    class_uri: str
    class_label: str

    display_label: str
    display_label_comment: str
    display_label_uri: str


    def __init__(self, uri: str = None, label: str = None, comment: str = None, is_literal: bool = False, is_blank: bool = False, class_uri: str = None, class_label: str = None) -> None:
        self.uri = uri
        self.label = label or uri
        self.comment = comment
        self.is_literal = is_literal
        self.is_blank = is_blank
        self.class_uri = class_uri
        self.class_label = class_label
        self.display_label = f"{self.label} ({self.class_label or self.class_uri})" if self.class_uri else f"{self.label}"
        self.display_label_comment = f"{self.display_label}: {self.comment}" if self.comment else self.display_label
        if len(self.display_label_comment) > 50:
            self.display_label_comment = self.display_label_comment[:50] + '...'
        self.display_label_uri = f"{self.label} - {self.uri}"


    def to_dict(self, prefix: str= '') -> dict:
        return {
            prefix + 'uri': self.uri,
            prefix + 'label': self.label,
            prefix + 'comment': self.comment,
            prefix + 'is_literal': self.is_literal,
            prefix + 'is_blank': self.is_blank,
            prefix + 'class_uri': self.class_uri,
            prefix + 'class_label': self.class_label,
            prefix + 'display_label': self.display_label,
            prefix + 'display_label_comment': self.display_label_comment,
            prefix + 'display_label_uri': self.display_label_uri
        }
    
    
    @staticmethod
    def from_dict(obj: dict, prefix: str= '') -> 'OntoEntity':

        # Handle boolean values as strings - For literal flag
        is_literal = obj.get(prefix + 'is_literal') or False
        if isinstance(is_literal, str):
            if is_literal.lower() == 'false': is_literal = False
            elif is_literal.lower() == 'true': is_literal = True

        # Handle boolean values as strings - For blank flag
        is_blank = obj.get(prefix + 'is_blank') or False
        if isinstance(is_blank, str):
            if is_blank.lower() == 'false': is_blank = False
            elif is_blank.lower() == 'true': is_blank = True

        return OntoEntity(
            uri=obj.get(prefix + 'uri'),
            label=obj.get(prefix + 'label'),
            comment=obj.get(prefix + 'comment'),
            is_literal=is_literal,
            is_blank=is_blank,
            class_uri=obj.get(prefix + 'class_uri'),
            class_label=obj.get(prefix + 'class_label')
        )