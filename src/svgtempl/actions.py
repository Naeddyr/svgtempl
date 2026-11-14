import enum


class StrEnum(enum.Enum):
    def __str__(self) -> str:
        return str(self.value)


class Act(StrEnum):
    OPEN = "file-open"
    SELECT = "select"
    QUIT = "quit"
    EXPORT_NAME = "export-filename"
    EXPORT_AREA_IS_PAGE = "export-area-page"
    EXPORT_DO = "export-do"
