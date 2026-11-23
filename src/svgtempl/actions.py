import enum


class StrEnum(enum.Enum):
    def __str__(self) -> str:
        return str(self.value)


class Act(StrEnum):
    QUIT = "quit"

    # META
    # Maybe knowing the inkscape version is useful if the 'API' changes
    VERSION = "inkscape-version"

    # FILE STUFF
    OPEN = "file-open"
    FROM_TEMPLATE = "file-new"
    FILE_CLOSE = "file-close"

    # SELECTION STUFF
    ADD = "select-by-id"
    SELECT_CLEAR = "select-clear"
    ADD_BY_CLASS = "select-by-class"
    ADD_BY_ELEMENT = "select-by-element"
    ADD_BY_CSS_SELECTOR = "select-by-selector"
    UNSELECT = "unselect-by-id"

    # INFORMATION
    # query-all 	Query 'x', 'y', 'width', and 'height'
    # Returns a list with all objects: id,x,y,width,height
    QUERY_ALL = "query-all"
    # Returns a list of id + "cloned: bool", "ref", "href", "total href"
    # XXX make this into a function
    PRINT_SELECT = "select-list"

    # These are not exactly needed...
    # They can be used to query just one selected object, by why?
    # Just query-all to get all the data in one.
    # query-height 	Query 'height' value(s) of object(s)
    # query-width 	Query 'width' value(s) of object(s)
    # query-x 	Query 'x' value(s) of selected objects
    # query-y 	Query 'y' value(s) of selected objects

    # EXPORT
    EXPORT_NAME = "export-filename"
    EXPORT_TYPE = "export-type"
    EXPORT_AREA_IS_PAGE = "export-area-page"
    EXPORT_DO = "export-do"

    # Transform stuff
    # Probably will only need rotate most of the time
    ROTATE = "transform-rotate"
    SCALE = "transform-scale"
    TRANSLATE = "transform-translate"

    DELETE = "delete-selection"

    # What the heck, add most.
    CLONE = "clone"
    CLONE_UNLINK = "clone-unlink"
    CLONE_UNLINK_RECURSIVELY = "clone-unlink-recursively"
    DUPLICATE = "duplicate"
    EDIT_REMOVE_FILTER = "edit-remove-filter"
    EXPORT_AREA_PAGE = "export-area-page"
    EXPORT_BACKGROUND = "export-background"
    EXPORT_BACKGROUND_OPACITY = "export-background-opacity"
    EXPORT_DPI = "export-dpi"
    EXPORT_HEIGHT = "export-height"
    EXPORT_MARGIN = "export-margin"
    EXPORT_OVERWRITE = "export-overwrite"
    EXPORT_PLAIN_SVG = "export-plain-svg"
    EXPORT_TEXT_TO_PATH = "export-text-to-path"
    EXPORT_USE_HINTS = "export-use-hints"
    EXPORT_WIDTH = "export-width"
    FILE_NEW = "file-new"
    INKSCAPE_VERSION = "inkscape-version"
    LAST_EFFECT = "last-effect"
    LAST_EFFECT_PREF = "last-effect-pref"
    OBJECT_ALIGN = "object-align"
    OBJECT_ALIGN_ON_CANVAS = "object-align-on-canvas"
    OBJECT_ALIGN_TEXT = "object-align-text"
    OBJECT_DISTRIBUTE = "object-distribute"
    OBJECT_DISTRIBUTE_TEXT = "object-distribute-text"
    OBJECT_FLIP_HORIZONTAL = "object-flip-horizontal"
    OBJECT_FLIP_VERTICAL = "object-flip-vertical"
    OBJECT_REARRANGE = "object-rearrange"
    OBJECT_RELEASE_CLIP = "object-release-clip"
    OBJECT_RELEASE_MASK = "object-release-mask"
    OBJECT_REMOVE_OVERLAPS = "object-remove-overlaps"
    OBJECT_ROTATE_90_CCW = "object-rotate-90-ccw"
    OBJECT_ROTATE_90_CW = "object-rotate-90-cw"
    OBJECT_SET_ATTRIBUTE = "object-set-attribute"
    OBJECT_SET_CLIP = "object-set-clip"
    OBJECT_SET_CLIP_GROUP = "object-set-clip-group"
    OBJECT_SET_INVERSE_CLIP = "object-set-inverse-clip"
    OBJECT_SET_INVERSE_MASK = "object-set-inverse-mask"
    OBJECT_SET_MASK = "object-set-mask"
    OBJECT_SET_PROPERTY = "object-set-property"
    OBJECT_STROKE_TO_PATH = "object-stroke-to-path"
    OBJECT_TO_PATH = "object-to-path"
    OBJECT_TO_PATTERN = "object-to-pattern"
    PATH_BREAK_APART = "path-break-apart"
    PATH_COMBINE = "path-combine"
    PATH_CUT = "path-cut"
    PATH_DIFFERENCE = "path-difference"
    PATH_DIVISION = "path-division"
    PATH_EXCLUSION = "path-exclusion"
    PATH_FILL_BETWEEN_PATHS = "path-fill-between-paths"
    PATH_INTERSECTION = "path-intersection"
    PATH_SIMPLIFY = "path-simplify"
    PATH_SPLIT = "path-split"
    PATH_UNION = "path-union"
    PATTERN_TO_OBJECT = "pattern-to-object"
    SELECT_ALL = "select-all"
    SELECT_INVERT = "select-invert"
    SELECTION_BOTTOM = "selection-bottom"
    SELECTION_GROUP = "selection-group"
    SELECTION_HIDE = "selection-hide"
    SELECTION_LINK = "selection-link"
    SELECTION_LOCK = "selection-lock"
    SELECTION_LOWER = "selection-lower"
    SELECTION_MAKE_BITMAP_COPY = "selection-make-bitmap-copy"
    SELECTION_RAISE = "selection-raise"
    SELECTION_STACK_DOWN = "selection-stack-down"
    SELECTION_STACK_UP = "selection-stack-up"
    SELECTION_TOP = "selection-top"
    SELECTION_UNGROUP = "selection-ungroup"
    SELECTION_UNGROUP_POP = "selection-ungroup-pop"
    SELECTION_UNHIDE = "selection-unhide"
    SELECTION_UNHIDE_BELOW = "selection-unhide-below"
    SELECTION_UNLOCK = "selection-unlock"
    SELECTION_UNLOCK_BELOW = "selection-unlock-below"
    SELECT_ORIGINAL = "select-original"
    TEXT_CONVERT_TO_REGULAR = "text-convert-to-regular"
    TEXT_FLOW_INTO_FRAME = "text-flow-into-frame"
    TEXT_FLOW_SUBTRACT_FRAME = "text-flow-subtract-frame"
    TEXT_PUT_ON_PATH = "text-put-on-path"
    TEXT_REMOVE_FROM_PATH = "text-remove-from-path"
    TEXT_UNFLOW = "text-unflow"
    TEXT_UNKERN = "text-unkern"
    TRANSFORM_GROW = "transform-grow"
    TRANSFORM_GROW_STEP = "transform-grow-step"
    TRANSFORM_REMOVE = "transform-remove"
    UNHIDE_ALL = "unhide-all"
    UNLOCK_ALL = "unlock-all"
    VACUUM_DEFS = "vacuum-defs"
