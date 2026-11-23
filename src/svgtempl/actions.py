import enum


class StrEnum(enum.Enum):
    def __str__(self) -> str:
        return str(self.value)


class Act(StrEnum):
    QUIT = "quit"

    # FILE STUFF
    OPEN = "file-open"
    FROM_TEMPLATE = "file-new"
    # FILE_CLOSE = "file-close"

    # SELECTION STUFF
    ADD = "select-by-id"
    SELECT_CLEAR = "select-clear"
    ADD_BY_CLASS = "select-by-class"
    ADD_BY_ELEMENT = "select-by-element"
    ADD_BY_CSS_SELECTOR = "select-by-selector"

    # INFORMATION
    # query-all 	Query 'x', 'y', 'width', and 'height'
    QUERY_ALL = "query-all"
    # Returns a list with all objects: id,x,y,width,height

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


# clone 	Create a clone (a copy linked to the original) of selected object
# clone-link 	Relink the selected clones to the object currently on the clipboard
# clone-link-lpe 	Creates a new path, applies the Clone original LPE, and refers it to the selected path
# clone-unlink 	Cut the selected clones' links to the originals, turning them into standalone objects
# clone-unlink-recursively 	Unlink all clones in the selection, even if they are in groups.
# delete 	Delete selected items, nodes or text.
# delete-selection 	Delete selected items
# duplicate 	Duplicate Selected Objects
# edit-remove-filter 	Remove any filters from selected objects
# export-area-page 	Export page area
# export-background 	Include background color in exported file
# export-background-opacity 	Include background opacity in exported file
# export-do 	Do export
# export-dpi 	Set export DPI
# export-filename 	Set export file name
# export-height 	Set export height
# export-margin 	Set additional export margin
# export-overwrite 	Allow to overwrite existing files during export
# export-plain-svg 	Export as plain SVG
# export-text-to-path 	Convert texts to paths in the exported file
# export-type 	Set export file type
# export-use-hints 	Export using saved hints
# export-width 	Set export width
# file-close 	Close active document
# file-new 	Open new document using template
# inkscape-version 	Print Inkscape version and exit
# last-effect 	Repeat the last extension with the same settings
# last-effect-pref 	Repeat the last extension with new settings
# object-align 	Align selected objects; usage
# object-align-on-canvas 	Enable on-canvas alignment handles.
# object-align-text 	Align selected text alignment points; usage
# object-distribute 	Distribute selected objects; usage
# object-distribute-text 	Distribute text alignment points; usage [vertical
# object-flip-horizontal 	Flip selected objects horizontally
# object-flip-vertical 	Flip selected objects vertically
# object-rearrange 	Rearrange selected objects; usage
# object-release-clip 	Remove clipping path from selection
# object-release-mask 	Remove mask from selection
# object-remove-overlaps 	Remove overlaps between objects
# object-rotate-90-ccw 	Rotate selection 90° counter-clockwise
# object-rotate-90-cw 	Rotate selection 90° clockwise
# object-set-attribute 	Set or update an attribute of selected objects; usage
# object-set-clip 	Apply clipping path to selection (using the topmost object as clipping path)
# object-set-clip-group 	Create a self-clipping group to which objects (not contributing to the clip-path) can be added
# object-set-inverse-clip 	Apply inverse clipping path to selection (Power Clip LPE)
# object-set-inverse-mask 	Apply inverse mask to selection (Power Mask LPE)
# object-set-mask 	Apply mask to selection (using the topmost object as mask)
# object-set-property 	Set or update a property on selected objects; usage
# object-stroke-to-path 	Convert strokes to paths
# object-to-path 	Convert shapes to paths
# object-to-pattern 	Convert selection to a rectangle with tiled pattern fill
# path-break-apart 	Break selected paths into subpaths
# path-combine 	Combine several paths into one
# path-cut 	Cut the bottom path's stroke into pieces, removing fill
# path-difference 	Create difference of selected paths (bottom minus top)
# path-division 	Cut the bottom path into pieces
# path-exclusion 	Create exclusive OR of selected paths (those parts that belong to only one path)
# path-fill-between-paths 	Create a fill object using the selected paths
# path-intersection 	Create intersection of selected paths
# path-simplify 	Simplify selected paths (remove extra nodes)
# path-split 	Split selected paths into non-overlapping sections
# path-union 	Create union of selected paths
# pattern-to-object 	Extract objects from a tiled pattern fill
# select-all 	Select all; options
# select-invert 	Invert selection; options
# selection-bottom 	Lower selection to bottom
# selection-group 	Group selected objects
# selection-hide 	Hide all selected objects
# selection-link 	Add an anchor to selected objects
# selection-lock 	Lock all selected objects
# selection-lower 	Lower selection one step
# selection-make-bitmap-copy 	Export selection to a bitmap and insert it into document
# selection-raise 	Raise selection one step
# selection-stack-down 	Move the selection down in the stack order
# selection-stack-up 	Move the selection up in the stack order
# selection-top 	Raise selection to top
# selection-ungroup 	Ungroup selected objects
# selection-ungroup-pop 	Pop selected objects out of group
# selection-unhide 	Unhide all selected objects
# selection-unhide-below 	Unhide all items inside selected objects
# selection-unlock 	Unlock all selected objects
# selection-unlock-below 	Unlock all items inside selected objects
# select-list 	Print a list of objects in current selection
# select-original 	Select the object to which the selected clone is linked
# text-convert-to-regular 	Convert flowed text to regular text object (preserves appearance)
# text-flow-into-frame 	Put text into a frame (path or shape), creating a flowed text linked to the frame object
# text-flow-subtract-frame 	Flow text around a frame (path or shape), only available for SVG 2.0 Flow text.
# text-put-on-path 	Put text on path
# text-remove-from-path 	Remove text from path
# text-unflow 	Remove text from frame (creates a single-line text object)
# text-unkern 	Remove all manual kerns and glyph rotations from a text object
# transform-grow 	Grow/shrink selected objects
# transform-grow-step 	Grow/shrink selected objects by multiple of step value
# transform-remove 	Remove any transforms from selected objects
# unhide-all 	Unhide all objects
# unlock-all 	Unlock all objects
# unselect-by-id 	Deselect by ID
# vacuum-defs 	Remove unused definitions (gradients, etc.)
