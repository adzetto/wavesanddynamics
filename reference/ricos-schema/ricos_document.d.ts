export type RicosDocument = {
    nodes: RootNode[];
    /** Data about the Ricos document, such as version. This property is applicable only when using the ricos content editor and is auto-generated. */
    metadata?: Metadata;
    /** Defines styles for nodes. For example, you can define general styling for `headerOne`, and then override some of the properties separately for a specific header. */
    documentStyle?: DocumentStyle;
};
export type NodeStyle = {
    /** The top padding value in pixels. */
    paddingTop?: string;
    /** The bottom padding value in pixels. */
    paddingBottom?: string;
    backgroundColor?: string;
};
/**
 * This object sets a default styling for a type of node throughout the entire Ricos Document. For example, we can set the text color for all Heading 1 nodes.
 * You can override the styling of Text nodes separately using [Decorations](#decorations).
 */
export type DocumentStyle = {
    /** Style for the H1 nodes. */
    headerOne?: TextNodeStyle;
    /** Style for the H2 nodes. */
    headerTwo?: TextNodeStyle;
    /** Style for the H3 nodes. */
    headerThree?: TextNodeStyle;
    /** Style for the H4 nodes. */
    headerFour?: TextNodeStyle;
    /** Style for the H5 nodes. */
    headerFive?: TextNodeStyle;
    /** Style for the H6 nodes. */
    headerSix?: TextNodeStyle;
    /** Style for the paragraph nodes. */
    paragraph?: TextNodeStyle;
    /** Style for the block quote nodes. */
    blockquote?: TextNodeStyle;
    /** Style for the codeblock nodes. */
    codeBlock?: TextNodeStyle;
};
export type TextNodeStyle = {
    decorations?: Decoration[];
    /**
     * Node style, such as padding.
     *  **Note:** This node requires the [lineSpacing](#plugins) plugin.
     */
    nodeStyle?: NodeStyle;
    /** Text line height. */
    lineHeight?: string;
};
export type Metadata = {
    /** Ricos document version. */
    version?: number;
    id?: any;
    createdTimestamp?: any;
    updatedTimestamp?: any;
};
export type TextStyle = {
    /** Text alignment. Possible values: <br> - `AUTO`: Text aligns itself automatically. <br> - `LEFT`: Text is aligned to the left. <br> - `RIGHT`: Text is aligned to the right. <br> - `CENTER`: Text is centered. <br> - `JUSTIFY`: Text is justified to both margins. Default: `AUTO`. */
    textAlignment?: TextStyle_TextAlignment;
    /** Vertical spacing between lines of text in an element. */
    lineHeight?: string;
};
export type TextStyle_TextAlignment = 'AUTO' | 'LEFT' | 'RIGHT' | 'CENTER' | 'JUSTIFY';
export declare const TextStyle_TextAlignment: {
    readonly AUTO: "AUTO";
    readonly LEFT: "LEFT";
    readonly RIGHT: "RIGHT";
    readonly CENTER: "CENTER";
    readonly JUSTIFY: "JUSTIFY";
};
/** Link object. */
export type Link = {
    /** Absolute URL for the linked document. */
    url?: string;
    /** Target Node ID, where the user is redirected after clicking the anchor. */
    anchor?: string;
    /** The HTML `target` attribute value for the link. This property defines where the linked document opens. Possible values: <br> `SELF` - Default. Opens the linked document in the same frame as the link.<br> `BLANK` - Opens the linked document in a new browser tab or window.<br> `PARENT` - Opens the linked document in the link's parent frame.<br> `TOP` - Opens the linked document in the full body of the link's browser tab or window. */
    target?: Link_Target;
    /** This object specifies the relationship between the current document and the linked document. */
    rel?: Link_Rel;
    /** A serialized object used for a custom or external link panel. */
    customData?: string;
};
export type Link_Target = 'SELF' | 'BLANK' | 'PARENT' | 'TOP';
export declare const Link_Target: {
    readonly SELF: "SELF";
    readonly BLANK: "BLANK";
    readonly PARENT: "PARENT";
    readonly TOP: "TOP";
};
export type Link_Rel = {
    /**
     * Indicates to search engine crawlers not to follow the link.
     *  Default: `false`
     */
    nofollow?: boolean;
    /**
     * Indicates to search engine crawlers that the link is a paid placement such as sponsored content or an advertisement.
     *  Default: `false`
     */
    sponsored?: boolean;
    /**
     * Indicates that this link is user-generated content and isn't necessarily trusted or endorsed by the page author.
     *  Default: `false`
     */
    ugc?: boolean;
    /** Indicates that this link protects referral information from being passed to the target website. */
    noreferrer?: boolean;
};
/** File source object. */
export type FileSource = {
    /** Absolute URL for the file's source. */
    url?: string;
    /** ID that's resolved to a URL by a resolver function. */
    id?: string;
    /**
     * Indicates whether the file's source is private.
     *  Default: `false`
     */
    private?: boolean;
};
export type Media = {
    /** Media data source. */
    src: FileSource;
    /** Media width in pixels. */
    width?: number;
    /** Media height in pixels. */
    height?: number;
    /** Media duration in seconds. Only relevant for audio and video files. */
    duration?: number;
};
export type Never = {
    _neverCreatedElement: any;
};
export type PluginContainerData = {
    /** Node width in a container when it's displayed. */
    width?: PluginContainerData_Width;
    /**
     * Node alignment in its container. Possible values:
     *  - `CENTER`
     *  - `LEFT`
     *  - `RIGHT`
     */
    alignment?: PluginContainerData_Alignment;
    /** Spoiler cover settings. */
    spoiler?: PluginContainerData_Spoiler;
    /** Node height in a container when it's displayed. */
    height?: PluginContainerData_Height;
    /**
     * Whether the text should wrap around the node when it's displayed. If `textWrap` is `false`, the node takes up the width of its container.
     *  Default: `true` for all node types except `DIVIDER`.
     */
    textWrap?: boolean;
};
export type PluginContainerData_Alignment = 'CENTER' | 'LEFT' | 'RIGHT';
export declare const PluginContainerData_Alignment: {
    readonly CENTER: "CENTER";
    readonly LEFT: "LEFT";
    readonly RIGHT: "RIGHT";
};
export type PluginContainerData_Spoiler = {
    /**
     * Whether the spoiler cover is enabled.
     *  Default: `false`
     */
    enabled?: boolean;
    /** Description displayed on top of the spoiler cover. */
    description?: string;
    /** Text of a button that removes the spoiler cover. */
    buttonText?: string;
};
/** The width of the node when it's displayed. */
export type PluginContainerData_Width = {
    /**
     * Width size of a node in a container. Possible values:
     *  - `CONTENT`: The width of the container matches the content width.
     *  - `SMALL`: A small width.
     *  - `ORIGINAL`: The width of the container matches the original image width. **Note:** This value is applicable for `imageData` containers only.
     *  `FULL_WIDTH`: The image container takes up the full width of the screen. **Note:** This value is applicable for `imageData` containers only.
     */
    size?: PluginContainerData_Width_Type;
    /** A custom width value in pixels. */
    custom?: string;
};
export type PluginContainerData_Width_Type = 'CONTENT' | 'SMALL' | 'ORIGINAL' | 'FULL_WIDTH';
export declare const PluginContainerData_Width_Type: {
    readonly CONTENT: "CONTENT";
    readonly SMALL: "SMALL";
    readonly ORIGINAL: "ORIGINAL";
    readonly FULL_WIDTH: "FULL_WIDTH";
};
export type PluginContainerData_Height = {
    /** A custom height value in pixels. */
    custom?: string;
};
export type Decoration = BoldDecoration | ItalicDecoration | UnderlineDecoration | SpoilerDecoration | AnchorDecoration | MentionDecoration | LinkDecoration | ColorDecoration | FontSizeDecoration;
export type Decoration_Type = 'BOLD' | 'ITALIC' | 'UNDERLINE' | 'SPOILER' | 'ANCHOR' | 'MENTION' | 'LINK' | 'COLOR' | 'FONT_SIZE';
export declare const Decoration_Type: {
    readonly BOLD: "BOLD";
    readonly ITALIC: "ITALIC";
    readonly UNDERLINE: "UNDERLINE";
    readonly SPOILER: "SPOILER";
    readonly ANCHOR: "ANCHOR";
    readonly MENTION: "MENTION";
    readonly LINK: "LINK";
    readonly COLOR: "COLOR";
    readonly FONT_SIZE: "FONT_SIZE";
};
/** Text that is styled to appear thicker and more prominent than normal text. */
export type BoldDecoration = {
    /**
     * Decoration type.
     *  Value: `BOLD`
     */
    type: 'BOLD';
    /** Font weight. Values are from `100` to `900`. */
    fontWeightValue?: number;
};
/** Text that is styled to appear slanted or italicized, which is typically used for emphasis, citations, or to distinguish certain types of content. */
export type ItalicDecoration = {
    /**
     * Decoration type.
     *  Value: `ITALIC`
     */
    type: 'ITALIC';
    /** Whether to enable the italic text. */
    italicData?: boolean;
};
/** Text that is styled with a line underneath it. */
export type UnderlineDecoration = {
    /**
     * Decoration type.
     *  Value: `UNDERLINE`
     */
    type: 'UNDERLINE';
    /** Whether to enable the underlined text. */
    underlineData?: boolean;
};
/** Text that is styled to appear blurred. <br> **Note:** This decoration requires the [spoiler](#plugins) plugin. */
export type SpoilerDecoration = {
    /**
     * Decoration type.
     *  Value: `SPOILER`
     */
    type: 'SPOILER';
    /** Spoiler details. */
    spoilerData?: SpoilerData;
};
/** Clickable text in a hyperlink. Rendered in a different color, indicating that it is a link that users can click to navigate to section in the same page. */
export type AnchorDecoration = {
    /**
     * Decoration type.
     *  Value: `ANCHOR`
     */
    type: 'ANCHOR';
    /** Anchor details. */
    anchorData?: AnchorData;
};
/** A piece of text that mentions a specific user, often in social media platforms, forums, or content management systems. <br> **Note:** This decoration requires the [mention](#plugins) plugin. */
export type MentionDecoration = {
    /**
     * Decoration type.
     *  Value: `MENTION`
     */
    type: 'MENTION';
    /** Anchor details. */
    mentionData?: MentionData;
};
/** Clickable text in a hyperlink. This text is what users see and click on to navigate to another web page or another resource. <br> **Note:** This decoration requires the [link](#plugins) plugin. */
export type LinkDecoration = {
    /**
     * Decoration type.
     *  Value: `LINK`
     */
    type: 'LINK';
    /** Link details. */
    linkData?: LinkData;
};
/** Text that is styled using background and text colors. <br> **Note:** This decoration requires the [colorDecoration](#plugins) plugin. */
export type ColorDecoration = {
    /**
     * Decoration type.
     *  Value: `COLOR`
     */
    type: 'COLOR';
    /** Color details. */
    colorData?: ColorData;
};
/** Text font size. */
export type FontSizeDecoration = {
    /**
     * Decoration type.
     *  Value: `FONT_SIZE`
     */
    type: 'FONT_SIZE';
    /** Font size details. */
    fontSizeData?: FontSizeData;
};
export type AnchorData = {
    /** Target Node ID, where the user is redirected after clicking the anchor. */
    anchor?: string;
};
export type ColorData = {
    /** Background color in a hexadecimal value. */
    background?: string;
    /** Text color in a hexadecimal value. */
    foreground?: string;
};
export type LinkData = {
    /** Link object. */
    link?: Link;
};
export type MentionData = {
    /** The display name of the mentioned user. */
    name?: string;
    /** The username of the mentioned user, appearing after the "@" character. */
    slug?: string;
    /** ID of the mentioned user. */
    id?: string;
};
export type FontSizeData = {
    /**
     * Font size units. Possible values:
     *  - `PX`: Size in pixels.
     *  - `EM`: Relative to the font size of the element (2em means 2 times the size of the current font)
     */
    unit?: FontSizeData_fontType;
    /** Font size value. */
    value?: number;
};
export type FontSizeData_fontType = 'PX' | 'EM';
export declare const FontSizeData_fontType: {
    readonly PX: "PX";
    readonly EM: "EM";
};
export type SpoilerData = {
    /** [Node ID](#node-ids). */
    id?: string;
};
/** Used to visually distinguish quoted or cited content from the surrounding text. When rendered, it is displayed as the quoted text with indentation or other styling to visually separate it from the surrounding content. */
export type BlockquoteNode = {
    /**
     * Node type.
     *  Value: `BLOCKQUOTE`
     */
    type: 'BLOCKQUOTE';
    nodes: ParagraphNode[];
    /** [Node ID](#node-ids). */
    id?: string;
    /** Blockquote details. */
    blockquoteData?: BlockquoteData;
    /**
     * Defines the blockquote style, such as padding and background color.
     *  **Note:** This node requires the [lineSpacing](#plugins) plugin for styling.
     */
    style?: NodeStyle;
};
export type BlockquoteData = {
    /**
     * Blockquote margin from the left side. Possible values are from `1` to `4`.
     *  The indentation is measured in relative to the font size *em* units, by the following formula: **indentation * 1.5**. For example, if indentation is `2`, then margin is equal to **3em**. Therefore the margin is 3 times the size of the font.
     */
    indentation?: number;
};
/** Used to present programming code snippets, markup, or other text-based content that should be displayed exactly as it appears, without any interpretation or formatting applied by the browser. When rendered, it is displayed as the code block with a monospaced font, preserving indentation, line breaks, and spacing as specified in the code. */
export type CodeBlockNode = {
    /**
     * Node type.
     *  Value: `CODE_BLOCK`
     */
    type: 'CODE_BLOCK';
    nodes?: TextNode[];
    /** [Node ID](#node-ids). */
    id?: string;
    /** Code block details. */
    codeBlockData?: CodeBlockData;
    /**
     * Defines the blockquote style, such as padding and background color.
     *  **Note:** This node requires the [lineSpacing](#plugins) plugin for styling.
     */
    style?: NodeStyle;
};
export type CodeBlockData = {
    /** Defines the text style, such as alignment and line height. */
    textStyle?: TextStyle;
};
/** Used to denote the heading or title of a section. Headings are hierarchical, with different levels indicating the relative importance of the heading in the content's structure. There are 6 levels of headings, where `1` is the highest level and `6` is the lowest. */
export type HeadingNode = {
    /**
     * Node type.
     *  Value: `HEADING`
     */
    type: 'HEADING';
    nodes?: TextNode[];
    /** [Node ID](#node-ids). */
    id?: string;
    /**
     * Defines the heading style, such as padding and background color.
     *  **Note:** This node requires the [lineSpacing](#plugins) plugin for styling.
     */
    style?: NodeStyle;
    /** Heading options. */
    headingData?: HeadingData;
};
export type HeadingData = {
    /** Heading size from `1` to `6`, where `1` is the highest level and `6` is the lowest. */
    level?: number;
    /** Defines the heading text style, such as text alignment and line height. */
    textStyle?: TextStyle;
    /**
     * Heading margin from the left side. Possible values are from `1` to `4`.
     *  The indentation is measured in relative to the font size *em* units, by the following formula: **indentation * 1.5**. For example, if indentation is `2`, then margin is equal to **3em**. Therefore the margin is 3 times the size of the font.
     */
    indentation?: number;
};
/** Presents a group of items in a sequentially numbered or lettered manner. Ordered lists are used to represent information that has a specific order or sequence. */
export type OrderedListNode = {
    /**
     * Node type.
     *  Value: `ORDERED_LIST`
     */
    type: 'ORDERED_LIST';
    nodes: ListItemNode[];
    /** [Node ID](#node-ids). */
    id?: string;
    /** Ordered list details. */
    orderedListData?: OrderedListData;
};
export type OrderedListData = {
    /**
     * List margin from the left side. Possible values are from `1` to `4`.
     *  The indentation is measured in relative to the font size *em* units, by the following formula: **indentation * 1.5**. For example, if indentation is `2`, then margin is equal to **3em**. Therefore the margin is 3 times the size of the font.
     */
    indentation?: number;
    /** An integer (ranging from 0 to 4) used to control the additional indentation level of an ordered or bulleted list node, beyond its original HTML-defined nesting. When offset is 0, the list node appears at its default nesting level; as the value increases from 1 to 4, the node is indented further, creating the visual impression of deeper nesting without altering the actual HTML structure. */
    offset?: number;
    /** An integer to start counting from for the list items, overriding the default start of 1. */
    start?: number;
};
/** Presents a group of items in a visually organized manner, where each item is preceded by a bullet point. Bulleted lists are commonly used to present unordered information. */
export type BulletedListNode = {
    /**
     * Node type.
     *  Value: `BULLETED_LIST`
     */
    type: 'BULLETED_LIST';
    nodes: ListItemNode[];
    /** [Node ID](#node-ids). */
    id?: string;
    /** Bulleted list details. */
    bulletedListData?: BulletedListData;
};
export type BulletedListData = {
    indentation?: number;
    /** An integer (ranging from 0 to 4) used to control the additional indentation level of an ordered or bulleted list node, beyond its original HTML-defined nesting. When `offset` is `0`, the list node appears at its default nesting level; as the value increases from 1 to 4, the node is indented further, creating the visual impression of deeper nesting without altering the actual HTML structure. */
    offset?: number;
};
export type ListItemNode = {
    /**
     * Node type.
     *  Value: `LIST_ITEM`
     */
    type: 'LIST_ITEM';
    nodes: ListItemChildNode[];
    /** [Node ID](#node-ids). */
    id?: string;
};
export type ListItemChildNode = ParagraphNode | HeadingNode | OrderedListNode | BulletedListNode | ImageNode | VideoNode | GifNode | GalleryNode;
/** Used to structure text content, providing a clear separation between different ideas or sections of text. They are rendered with default styling that typically includes some space above and below the paragraph, making it visually distinct from the surrounding content. */
export type ParagraphNode = {
    /**
     * Node type.
     *  Value: `PARAGRAPH`
     */
    type: 'PARAGRAPH';
    nodes?: TextNode[];
    /** [Node ID](#node-ids). */
    id?: string;
    /**
     * Paragraphs vertical padding.
     *  **Note:** This node requires the [lineSpacing](#plugins) plugin for styling.
     */
    style?: NodeStyle;
    /** Paragraph node attributes. */
    paragraphData?: ParagraphData;
};
export type ParagraphData = {
    /** Styling for the paragraph text. */
    textStyle?: TextStyle;
    /** Paragraph margin from the left side. Possible values are from `1` to `4`. <br>Actual indentation is equal to **indentation * 40px**. */
    indentation?: number;
    /** Paragraph level for future different paragraphs */
    level?: number;
};
/** Text nodes hold the text itself (think `span` tag in HTML). The difference between `TextNode` and HTML `span` is that text nodes can't be nested and must contain non-empty string. Their appearance and behavior can be modified using [decorations](#decorations). */
export type TextNode = {
    /**
     * Node type.
     *  Value: `TEXT`
     */
    type: 'TEXT';
    /** Text options. */
    textData: TextData;
    /** [Node ID](#node-ids). */
    id?: string;
    nodes?: never[];
};
export type TextData = {
    /** A piece of text, possibly enhanced with additional decorations. Must not be empty. */
    text: string;
    decorations?: Decoration[];
};
/** Similar to `LinkPreviewNode`, this node is used to embed external content preview, but from Wix business solutions. You can embed previews from the Wix Bookings, Wix Stores and Wix Events apps. */
export type AppEmbedNode = {
    /**
     * Node type.
     *  Value: `APP_EMBED`
     */
    type: 'APP_EMBED';
    /** [Node ID](#node-ids). */
    id?: string;
    /** Embedded Wix app details. */
    appEmbedData?: AppEmbedData;
    nodes?: never[];
};
export type AppEmbedData = AppEmbedDataProduct | AppEmbedDataEvent | AppEmbedDataBooking;
export type AppEmbedData_AppType = 'PRODUCT' | 'EVENT' | 'BOOKING';
export declare const AppEmbedData_AppType: {
    readonly PRODUCT: "PRODUCT";
    readonly EVENT: "EVENT";
    readonly BOOKING: "BOOKING";
};
/** Wix Stores app. Embeds a particular product. */
export type AppEmbedDataProduct = {
    /**
     * Which Wix App to embed. Possible values:
     *  - `PRODUCT`: Wix Stores app. Embeds a particular product.
     *  - `EVENT`: Wix Events app. Embeds a particular event.
     *  - `BOOKINGS`: Wix Bookings app. Embeds a particular booking.
     */
    type: 'PRODUCT';
    /** Embedded content name. */
    name: string;
    /** Embedded content thumbnail. */
    image: Media;
    /** Embedded content ID. */
    itemId?: string;
    /** Embedded content URL. */
    url?: string;
    /** Deprecated: Use `image` instead. */
    imageSrc?: string;
};
/** Wix Events app. Embeds a particular event. */
export type AppEmbedDataEvent = {
    type: 'EVENT';
    /** Embedded content name. */
    name: string;
    /** Embedded content thumbnail. */
    image: Media;
    /** Embedded Wix Events app content. */
    eventData: AppEmbedData_EventData;
    /** Embedded content ID. */
    itemId?: string;
    /** Embedded content URL. */
    url?: string;
    /** Deprecated: Use `image` instead. */
    imageSrc?: string;
};
/** Wix Bookings app. Embeds a particular booking. */
export type AppEmbedDataBooking = {
    type: 'BOOKING';
    /** Embedded content name. */
    name: string;
    /** Embedded content thumbnail. */
    image: Media;
    /** Embedded content ID. */
    itemId?: string;
    /** Embedded content URL. */
    url?: string;
    /** Embedded Wix Bookings app content. */
    bookingData?: AppEmbedData_BookingData;
    /** Deprecated: Use `image` instead. */
    imageSrc?: string;
};
export type AppEmbedData_BookingData = {
    /** Booking duration in minutes. */
    durations?: string;
};
export type AppEmbedData_EventData = {
    /** Event schedule. */
    scheduling?: string;
    /** Event location. */
    location?: string;
};
/** A multimedia node used to embed and play audio content directly in a webpage. When rendered, it is displayed as the audio player with the specified audio file (can be a platform such as Spotify or Soundloud, and Wix Media). Users can interact with the controls to play, pause, rewind, and adjust the volume of the audio. */
export type AudioNode = {
    /**
     * Node type.
     *  Value: `AUDIO`
     */
    type: 'AUDIO';
    /** [Node ID](#node-ids). */
    id?: string;
    /** Audio details. */
    audioData?: AudioData;
    nodes?: never[];
};
export type AudioData = {
    /** Audio node container styling. */
    containerData?: PluginContainerData;
    /** Audio file details. */
    audio?: Media;
    /**
     * Sets whether the audio download button is disabled.
     *  Default: `false`
     */
    disableDownload?: boolean;
    /** Cover image. */
    coverImage?: Media;
    /** Track name. */
    name?: string;
    /** Author name. */
    authorName?: string;
    /** An HTML version of the audio node. */
    html?: string;
};
/** A node that is used to trigger an action when clicked or activated. */
export type ButtonNode = {
    /**
     * Node type.
     *  Value: `BUTTON`
     */
    type: 'BUTTON';
    /** Button details. */
    buttonData: ButtonData;
    /** [Node ID](#node-ids). */
    id?: string;
    nodes?: never[];
};
export type ButtonData = {
    /** Button type. Possible values: <br> - `LINK`: When clicked, a user is redirected. <br> - `ACTION`: When clicked, performs an action. */
    type: ButtonData_Type;
    /** Button text. */
    text: string;
    /**  Button container styling. */
    containerData?: PluginContainerData;
    /** Button styling. */
    styles?: ButtonData_Styles;
    /** Button link details. */
    link?: Link;
};
export type ButtonData_Type = 'LINK' | 'ACTION';
export declare const ButtonData_Type: {
    readonly LINK: "LINK";
    readonly ACTION: "ACTION";
};
export type ButtonData_Styles = {
    /** Border properties. */
    border?: ButtonData_Styles_Border;
    /** Color properties. */
    colors?: ButtonData_Styles_Colors;
};
export type ButtonData_Styles_Colors = {
    /** The text color in a hexadecimal value. */
    text?: string;
    /** The border color in a hexadecimal value. */
    border?: string;
    /** The background color in a hexadecimal value. */
    background?: string;
};
export type ButtonData_Styles_Border = {
    /** Border width in pixels. */
    width?: number;
    /** Border radius in pixels. */
    radius?: number;
};
/** A list of items where each item can be expanded or collapsed to reveal or hide additional content associated with it. */
export type CollapsibleListNode = {
    /**
     * Node type.
     *  Value: `COLLAPSIBLE_LIST`
     */
    type: 'COLLAPSIBLE_LIST';
    nodes: CollapsibleItemNode[];
    /** [Node ID](#node-ids). */
    id?: string;
    /** Collapsible list details. */
    collapsibleListData?: CollapsibleListData;
};
export type CollapsibleListData = {
    /** Collapsible list container styling. */
    containerData?: PluginContainerData;
    /**
     * Whether only one item can be expanded at a time.
     *  Default: `false`
     */
    expandOnlyOne?: boolean;
    /**
     * Sets which items are automatically expanded after the page loads. Possible values:
     *  - `FIRST`
     *  - `ALL`
     *  - `NONE`
     */
    initialExpandedItems?: 'FIRST' | 'ALL' | 'NONE';
    /**
     * Direction of the text in the list. Possible values:
     *  - `LTR`: Left to right.
     *  - `RTL`: Right to left.
     */
    direction?: CollapsibleListData_Direction;
    /** Whether the collapsible item will appear in search results as a FAQ. */
    isQapageData?: boolean;
};
export type CollapsibleListData_Direction = 'LTR' | 'RTL';
export declare const CollapsibleListData_Direction: {
    readonly LTR: "LTR";
    readonly RTL: "RTL";
};
export type CollapsibleItemNode = {
    /**
     * Node type.
     *  Value: `COLLAPSIBLE_ITEM`
     */
    type: 'COLLAPSIBLE_ITEM';
    nodes: CollapsibleItemChildNode[];
    /** [Node ID](#node-ids). */
    id?: string;
};
export type CollapsibleItemChildNode = CollapsibleItemTitleNode | CollapsibleItemBodyNode;
/** Collapsible list item title node. */
export type CollapsibleItemTitleNode = {
    /**
     * Node type.
     *  Value: `COLLAPSIBLE_ITEM_TITLE`
     */
    type: 'COLLAPSIBLE_ITEM_TITLE';
    nodes: CollapsibleTitleChildNode[];
    /** [Node ID](#node-ids). */
    id?: string;
};
export type CollapsibleTitleChildNode = ParagraphNode | HeadingNode | BulletedListNode | OrderedListNode | BlockquoteNode | CodeBlockNode;
/** Collapsible list item body node. */
export type CollapsibleItemBodyNode = {
    /**
     * Node type.
     *  Value: `COLLAPSIBLE_ITEM_BODY`
     */
    type: 'COLLAPSIBLE_ITEM_BODY';
    nodes: CollapsibleItemBodyChildNode[];
    /** [Node ID](#node-ids). */
    id?: string;
};
/** Collapsible list item body node. */
export type CollapsibleItemBodyChildNode = ParagraphNode | HeadingNode | BulletedListNode | OrderedListNode | BlockquoteNode | AudioNode | FileNode | ImageNode | VideoNode | GifNode | DividerNode | CodeBlockNode | AppEmbedNode | LinkPreviewNode | GalleryNode | ButtonNode | CollapsibleListNode | TableNode | EmbedNode | PollNode | HtmlNode;
/** A visual node that is used to separate content sections in a page. When rendered, it is displayed as a horizontal line between the paragraphs, acting as a divider between them. */
export type DividerNode = {
    /**
     * Node type.
     *  Value: `DIVIDER`
     */
    type: 'DIVIDER';
    /** [Node ID](#node-ids). */
    id?: string;
    /** Divider details. */
    dividerData?: DividerData;
    nodes?: never[];
};
export type DividerData = {
    /** Divider container styling. */
    containerData?: PluginContainerData;
    /** Divider line style. Possible values: <br> - `SINGLE` <br> - `DOUBLE` <br> - `DASHED` <br> - `DOTTED` */
    lineStyle?: DividerData_LineStyle;
    /** Divider width. Possible values: <br> - `LARGE` <br> - `MEDIUM` <br> - `SMALL` */
    width?: DividerData_Width;
    /** Divider alignment. Possible values: <br> - `CENTER` <br> - `LEFT` <br> - `RIGHT` */
    alignment?: DividerData_Alignment;
};
export type DividerData_LineStyle = 'SINGLE' | 'DOUBLE' | 'DASHED' | 'DOTTED';
export declare const DividerData_LineStyle: {
    readonly SINGLE: "SINGLE";
    readonly DOUBLE: "DOUBLE";
    readonly DASHED: "DASHED";
    readonly DOTTED: "DOTTED";
};
export type DividerData_Width = 'LARGE' | 'MEDIUM' | 'SMALL';
export declare const DividerData_Width: {
    readonly LARGE: "LARGE";
    readonly MEDIUM: "MEDIUM";
    readonly SMALL: "SMALL";
};
export type DividerData_Alignment = 'CENTER' | 'LEFT' | 'RIGHT';
export declare const DividerData_Alignment: {
    readonly CENTER: "CENTER";
    readonly LEFT: "LEFT";
    readonly RIGHT: "RIGHT";
};
/** Similar to `HtmlNode`, this node is used to display embedded content when you post a link to that resource, without having to parse the resource directly. It provides a standardized way for web developers to include content such as videos, images, and other multimedia elements from supported providers without needing to handle the complex embedding code themselves. For more information, read [oembed](https://oembed.com/). */
export type EmbedNode = {
    /**
     * Node type.
     *  Value: `EMBED`
     */
    type: 'EMBED';
    /** oEmbed details. */
    embedData: EmbedData;
    /** [Node ID](#node-ids). */
    id?: string;
    nodes?: never[];
};
export type EmbedData = {
    /** oEmbed node container styling. */
    containerData?: PluginContainerData;
    /** [oEmbed](https://www.oembed.com) details. */
    oembed?: Oembed;
    /** Original asset source. */
    src?: string;
};
export type Oembed = {
    /** Resource type. For more information read the [oEmbed](https://www.oembed.com) official website. */
    type?: string;
    /** Width of the resource specified in the `url` field in pixels. */
    width?: number;
    /** Height of the resource specified in the `url` field in pixels. */
    height?: number;
    /** A text title, describing the resource. */
    title?: string;
    /** The source URL for the resource. */
    url?: string;
    /** HTML required to embed a video player. The HTML should have no padding or margins. */
    html?: string;
    /** Name of the author or owner of the resource. */
    authorName?: string;
    /** URL for the author or owner of the resource. */
    authorUrl?: string;
    /** Name of the resource provider. */
    providerName?: string;
    /** URL for the resource provider. */
    providerUrl?: string;
    /** URL for a thumbnail image for the resource. If this property is defined, `thumbnailWidth` and `thumbnailHeight` must also be defined. */
    thumbnailUrl?: string;
    /** Width of the resource's thumbnail image. If this property is defined, `thumbnailUrl` and `thumbnailHeight` must also be defined. */
    thumbnailWidth?: string;
    /** Height of the resource's thumbnail image. If this property is defined, `thumbnailUrl` and `thumbnailWidth`must also be defined. */
    thumbnailHeight?: string;
    /** URL for an embedded video. */
    videoUrl?: string;
    /** The oEmbed version number.  This value must be `1.0`. */
    version?: string;
};
/** A digital file stored on a computer that is uploaded and accessed in a page. Files can include various types of content, such as text documents, images, videos, and so on. */
export type FileNode = {
    /**
     * Node type.
     *  Value: `FILE`
     */
    type: 'FILE';
    /** File details. */
    fileData: FileData;
    /** [Node ID](#node-ids). */
    id?: string;
    nodes?: never[];
};
export type FileData = {
    /** File container styling. */
    containerData?: PluginContainerData;
    /** File data source. */
    src?: FileSource;
    /** File name. */
    name?: string;
    /** File type. */
    type?: string;
    /** Deprecated. Replaced by sizeInKb */
    size?: number;
    /** File size in KB. */
    sizeInKb?: string;
    /** Settings for PDF files. */
    pdfSettings?: FileData_PDFSettings;
    /** File MIME type. */
    mimeType?: string;
    /** File path. */
    path?: string;
};
export type FileData_PDFSettings = {
    /**
     * PDF view mode. Possible values:
     *  - `NONE`: The PDF isn't displayed.
     *  - `FULL`: A full PDF page view is displayed.
     *  - `MINI`: A mini view of the PDF is displayed.
     */
    viewMode?: FileData_PDFSettings_ViewMode;
    /**
     * Whether the PDF download button is disabled.
     *  Default: `false`
     */
    disableDownload?: boolean;
    /**
     * Whether the PDF print button is disabled.
     *  Default: `false`
     */
    disablePrint?: boolean;
};
export type FileData_PDFSettings_ViewMode = 'NONE' | 'FULL' | 'MINI';
export declare const FileData_PDFSettings_ViewMode: {
    readonly NONE: "NONE";
    readonly FULL: "FULL";
    readonly MINI: "MINI";
};
/** A collection of images displayed together in a visually appealing and organized manner. */
export type GalleryNode = {
    /**
     * Node type.
     *  Value: `GALLERY`
     */
    type: 'GALLERY';
    /** Gallery node details. */
    galleryData: GalleryData;
    /** [Node ID](#node-ids). */
    id?: string;
    nodes?: never[];
};
export type GalleryData = {
    items: GalleryData_Item[];
    /** Gallery container styling. */
    containerData?: PluginContainerData;
    /** Gallery appearance options. */
    options?: GalleryOptions;
    /** Whether the expand button is disabled. Default: `false` */
    disableExpand?: boolean;
    /** Whether the download button is disabled. Default: `false` */
    disableDownload?: boolean;
};
export type GalleryOptions = {
    /** Gallery layout. */
    layout?: GalleryOptions_Layout;
    /** Styling for gallery items. */
    item?: GalleryOptions_ItemStyle;
    /** Styling for gallery thumbnail images. */
    thumbnails?: GalleryOptions_Thumbnails;
};
export type GalleryOptions_Layout = {
    /** Gallery layout type. Possible values: <br> - `COLLAGE`: Presents images in various sizes and positions, creating an artistic or dynamic layout. <br> - `MASONRY`: A grid-based design that places items in optimal positions based on available vertical space, creating an arrangement where items of varying heights fit together like bricks in a wall. <br> - `GRID`: A layout structure that organizes items into rows and columns, creating a clean, uniform, and visually appealing arrangement of images. <br> - `THUMBNAIL`: A smaller, scaled-down version of an image that serves as a preview. <br> - `SLIDER`: A component that allows users to browse through a set of images by sliding or swiping through them, typically in a confined viewing area. <br> - `SLIDESHOW`: A component that automatically or manually transitions through a set of images in a designated area. <br> - `PANORAMA`: Wide-angle or 360-degree image that allows users to view an extended horizontal view of a scene. <br> - `COLUMN`: Arrangement of the gallery items in vertical sections. <br> - `MAGIC`: Visually stunning, dynamic effects that enhance the user experience. <br> - `FULLSIZE`: A layout where each image or item is displayed at its full size, taking up the entire viewport or a significant portion of the screen.. */
    type?: GalleryOptions_Layout_Type;
    /** Whether the horizontal scroll is enabled. Default: `true`, unless the `type` field is set to `GRID` or `COLLAGE`. */
    horizontalScroll?: boolean;
    /** Gallery orientation. Possible values: <br> - `ROWS`: Gallery items are arranged horizontally in rows. <br> - `COLUMNS`: Gallery items are arranged vertically in columns. */
    orientation?: GalleryOptions_Layout_Orientation;
    /** The number of columns to display on computer screens. */
    numberOfColumns?: number;
    /** The number of columns to display on mobile phone screens. */
    mobileNumberOfColumns?: number;
};
export type GalleryOptions_Layout_Type = 'COLLAGE' | 'MASONRY' | 'GRID' | 'THUMBNAIL' | 'SLIDER' | 'SLIDESHOW' | 'PANORAMA' | 'COLUMN' | 'MAGIC' | 'FULLSIZE';
export declare const GalleryOptions_Layout_Type: {
    readonly COLLAGE: "COLLAGE";
    readonly MASONRY: "MASONRY";
    readonly GRID: "GRID";
    readonly THUMBNAIL: "THUMBNAIL";
    readonly SLIDER: "SLIDER";
    readonly SLIDESHOW: "SLIDESHOW";
    readonly PANORAMA: "PANORAMA";
    readonly COLUMN: "COLUMN";
    readonly MAGIC: "MAGIC";
    readonly FULLSIZE: "FULLSIZE";
};
export type GalleryOptions_Layout_Orientation = 'ROWS' | 'COLUMNS';
export declare const GalleryOptions_Layout_Orientation: {
    readonly ROWS: "ROWS";
    readonly COLUMNS: "COLUMNS";
};
export type GalleryOptions_ItemStyle = {
    /** Dimension for each gallery item in pixels (behavaior changes according to a gallery type). */
    targetSize?: number;
    /** Item ratio */
    ratio?: number;
    /** Sets how gallery item images are cropped. Possible values: <br> - `FILL`: Each item in the gallery is cropped and resized to completely fill its container, ensuring that no empty space is left while maintaining the aspect ratio of the original image. <br> - `FIT`: Each item in the gallery is resized to fit entirely in its container without any cropping. */
    crop?: GalleryOptions_ItemStyle_Crop;
    /** The spacing between gallery items in pixels. */
    spacing?: number;
};
export type GalleryOptions_ItemStyle_Crop = 'FILL' | 'FIT';
export declare const GalleryOptions_ItemStyle_Crop: {
    readonly FILL: "FILL";
    readonly FIT: "FIT";
};
export type GalleryOptions_Thumbnails = {
    /** Thumbnail alignment. Possible values: <br> - `TOP` <br> - `RIGHT` <br> - `BOTTOM` <br> - `LEFT` <br> - `NONE` */
    placement?: GalleryOptions_Thumbnails_Alignment;
    /** Spacing between thumbnails in pixels. */
    spacing?: number;
};
export type GalleryOptions_Thumbnails_Alignment = 'TOP' | 'RIGHT' | 'BOTTOM' | 'LEFT' | 'NONE';
export declare const GalleryOptions_Thumbnails_Alignment: {
    readonly TOP: "TOP";
    readonly RIGHT: "RIGHT";
    readonly BOTTOM: "BOTTOM";
    readonly LEFT: "LEFT";
    readonly NONE: "NONE";
};
export type GalleryData_Item = {
    /** Item title. */
    title?: string;
    /** Item's alternative text. */
    altText?: string;
    /** Image item. */
    image?: GalleryData_Item_Image;
    /** Video item. */
    video?: GalleryData_Item_Video;
};
export type GalleryData_Item_Video = {
    /** Video file details. */
    media: Media;
    /** Video thumbnail file details. */
    thumbnail?: Media;
};
export type GalleryData_Item_Image = {
    /** Image file details. */
    media: Media;
    /** Link details for images that are links. */
    link?: Link;
};
/** GIF images are made up of a series of frames, allowing them to display animations or short video clips without the need for additional plugins or technologies. */
export type GifNode = {
    /**
     * Node type.
     *  Value: `GIF`
     */
    type: 'GIF';
    /** GIF details. */
    gifData: GIFData;
    /** [Node ID](#node-ids). */
    id?: string;
    nodes?: never[];
};
export type GIFData = {
    /** Styling for the GIF container, such as dimensions and alignment. */
    containerData?: PluginContainerData;
    /** Source for the full size GIF. */
    original?: GIF;
    /** Source for the downsized GIF. */
    downsized?: GIF;
    /** Height in pixels. */
    height?: number;
    /** Width in pixels. */
    width?: number;
};
export type GIF = {
    /** URL for a file in GIF format. */
    gif?: string;
    /** URL for a file in MP4 format. */
    mp4?: string;
    /** GIF thumbnail URL. */
    still?: string;
};
/** Incorporates external content, such as interactive maps, or entire web pages. */
export type HtmlNode = {
    /**
     * Node type.
     *  Value: `HTML`
     */
    type: 'HTML';
    /** HTML details. */
    htmlData: HTMLData;
    /** [Node ID](#node-ids). */
    id?: string;
    nodes?: never[];
};
export type HTMLData = {
    /** HTML node container styling. */
    containerData?: PluginContainerData;
    /**
     * HTML code type. Possible values:
     *  - `HTML`: HTML code.
     *  - [`ADSENSE`](https://adsense.google.com/start/): A service provided by Google for serving advertisements on web pages.
     */
    source?: HTMLData_Source;
    /** HTML code URL. */
    url?: string;
    /** HTML code. */
    html?: string;
};
export type HTMLData_Source = 'HTML' | 'ADSENSE';
export declare const HTMLData_Source: {
    readonly HTML: "HTML";
    readonly ADSENSE: "ADSENSE";
};
/** Displays standalone pictures in a page. */
export type ImageNode = {
    /**
     * Node type.
     *  Value: `IMAGE`
     */
    type: 'IMAGE';
    /** Image options. */
    imageData: ImageData;
    /** [Node ID](#node-ids). */
    id?: string;
    nodes?: never[];
};
export type ImageData = {
    /** Image file details, such as source and dimensions. */
    image: Media;
    /** Styling for the image container, such as dimensions and alignment. */
    containerData?: PluginContainerData;
    /** Link details, such as URL, or anchor, if image is also used as a link. */
    link?: Link;
    /**
     * Whether the image expands to the full screen when clicked.
     *  Default: `false`
     */
    disableExpand?: boolean;
    /** An alternate text for an image. Used for improved accessibility and shown when the image can't be displayed. */
    altText?: string;
    /** Image title. */
    caption?: string;
    /**
     * Whether the download image button is disabled.
     *  Default: `false`
     */
    disableDownload?: boolean;
};
/** A preview or summary of a webpage. Link previews include elements such as the title of the linked page, a brief description or excerpt of the content, and possibly a thumbnail image or other relevant information. */
export type LinkPreviewNode = {
    /**
     * Node type.
     *  Value: `LINK_PREVIEW`
     */
    type: 'LINK_PREVIEW';
    /** Link preview details. */
    linkPreviewData: LinkPreviewData;
    /** [Node ID](#node-ids). */
    id?: string;
    nodes?: never[];
};
export type LinkPreviewData = {
    /** Link preview container styling. */
    containerData?: PluginContainerData;
    /** Link details. */
    link?: Link;
    /** Preview title. */
    title?: string;
    /** Preview thumbnail URL. */
    thumbnailUrl?: string;
    /** Preview description. */
    description?: string;
    /** Preview content as HTML. */
    html?: string;
};
/** A node that allows users to vote or express their opinions on a particular question, topic, or issue. */
export type PollNode = {
    /**
     * Node type.
     *  Value: `POLL`
     */
    type: 'POLL';
    /** Poll details. */
    pollData: PollData;
    /** [Node ID](#node-ids). */
    id?: string;
    nodes?: never[];
};
export type PollData = {
    /** Poll container styling. */
    containerData?: PluginContainerData;
    /** Poll data. */
    poll?: PollData_Poll;
    /** Poll layout settings. */
    layout?: PollData_Layout;
    /** Poll design. */
    design?: PollData_Design;
};
export type PollData_Poll = {
    /** [Node ID](#node-ids). */
    id?: string;
    /** Poll title. */
    title?: string;
    /** Poll creator ID. */
    creatorId?: string;
    /** Main poll image. */
    image?: Media;
    options?: PollData_Poll_Option[];
    /** Poll display settings. */
    settings?: PollData_Poll_Settings;
};
export type PollData_Poll_Option = {
    /** Poll option ID. */
    id?: string;
    /** Poll option title */
    title?: string;
    /** Image displayed with the option. */
    image?: Media;
};
export type PollData_Poll_Settings = {
    /** Permission settings for voting. */
    permissions?: PollData_Poll_Settings_Permissions;
    /**
     * Whether to display the voters in the vote results.
     *  Default: `true`.
     */
    showVoters?: boolean;
    /**
     * Whether to display the vote count.
     *  Default: `true`.
     */
    showVotesCount?: boolean;
};
export type PollData_Poll_Settings_Permissions = {
    /**
     * Who can view the poll results. Possible values:
     *  - `CREATOR`: Only poll creator can see the results.
     *  - `VOTERS`: Only voters can see the results.
     *  - `EVERYONE`: Anyone who visits the site can see the results.
     */
    view?: PollData_Poll_Settings_Permissions_ViewRole;
    /**
     * Who can vote. Possble values:
     *  - `SITE_MEMBERS`: Only site members can vote.
     *  - `ALL`: All site visitors can vote.
     */
    vote?: PollData_Poll_Settings_Permissions_VoteRole;
    /**
     * Whether one site visitor can vote multiple times.
     *  Default: `false`
     */
    allowMultipleVotes?: boolean;
};
export type PollData_Poll_Settings_Permissions_ViewRole = 'CREATOR' | 'VOTERS' | 'EVERYONE';
export declare const PollData_Poll_Settings_Permissions_ViewRole: {
    readonly CREATOR: "CREATOR";
    readonly VOTERS: "VOTERS";
    readonly EVERYONE: "EVERYONE";
};
export type PollData_Poll_Settings_Permissions_VoteRole = 'SITE_MEMBERS' | 'ALL';
export declare const PollData_Poll_Settings_Permissions_VoteRole: {
    readonly SITE_MEMBERS: "SITE_MEMBERS";
    readonly ALL: "ALL";
};
export type PollData_Layout = {
    /** Poll layout settings. */
    poll?: PollData_Layout_PollLayout;
    /** Poll options layout settings. */
    options?: PollData_Layout_OptionLayout;
};
export type PollData_Layout_PollLayout = {
    /** Voting options layout. Possible values: <br> - `LIST`: Options are displayed as a list. <br> - `GRID`: Options are displayed in a grid.. */
    type?: PollData_Layout_PollLayout_Type;
    /** Direction of the text in the poll. Possible values: <br> - `LTR`: Left to right. <br> - `RTL`: Right to left. */
    direction?: PollData_Layout_PollLayout_Direction;
    /**
     * Whether to display the main poll image.
     *  Default: `false`
     */
    enableImage?: boolean;
};
export type PollData_Layout_PollLayout_Type = 'LIST' | 'GRID';
export declare const PollData_Layout_PollLayout_Type: {
    readonly LIST: "LIST";
    readonly GRID: "GRID";
};
export type PollData_Layout_PollLayout_Direction = 'LTR' | 'RTL';
export declare const PollData_Layout_PollLayout_Direction: {
    readonly LTR: "LTR";
    readonly RTL: "RTL";
};
export type PollData_Layout_OptionLayout = {
    /**
     * Whether to display option images.
     *  Defaults: `false`.
     */
    enableImage?: boolean;
};
export type PollData_Design = {
    /** Poll styling. */
    poll?: PollData_Design_PollDesign;
    /** Voting options styling. */
    options?: PollData_Design_OptionDesign;
};
export type PollData_Design_PollDesign = {
    /** Poll background styling. */
    background?: PollData_Design_PollDesign_Background;
    /** Border radius in pixels. */
    borderRadius?: number;
};
export type PollData_Design_PollDesign_Background = PollData_Background_ColorVariant | PollData_Background_ImageVariant | PollData_Background_GradientVariant;
export type PollData_Design_PollDesign_Background_Type = 'COLOR' | 'IMAGE' | 'GRADIENT';
export declare const PollData_Design_PollDesign_Background_Type: {
    readonly COLOR: "COLOR";
    readonly IMAGE: "IMAGE";
    readonly GRADIENT: "GRADIENT";
};
export type PollData_Background_ColorVariant = {
    type: 'COLOR';
    /** The background color in a hexademical value. */
    color?: string;
};
export type PollData_Background_ImageVariant = {
    type: 'IMAGE';
    /** Image to use for the background. */
    image?: Media;
};
export type PollData_Background_GradientVariant = {
    type: 'GRADIENT';
    /** Gradient background details. */
    gradient?: PollData_Design_PollDesign_Background_Gradient;
};
export type PollData_Design_PollDesign_Background_Gradient = {
    /** Gradient angle in degrees. */
    angle?: number;
    /** Start color as a hexadecimal value. */
    startColor?: string;
    /** end color as a hexadecimal value. */
    lastColor?: string;
};
export type PollData_Design_OptionDesign = {
    /** Border radius in pixels. */
    borderRadius?: number;
};
/** A structural node used to display data in rows and columns. */
export type TableNode = {
    /**
     * Node type.
     *  Value: `TABLE`
     */
    type: 'TABLE';
    nodes: TableRowNode[];
    /** [Node ID](#node-ids). */
    id?: string;
    /** Table details. */
    tableData?: TableData;
};
export type TableRowNode = {
    /**
     * Node type.
     *  Value: `TABLE_ROW`
     */
    type: 'TABLE_ROW';
    nodes: TableCellNode[];
    /** [Node ID](#node-ids). */
    id?: string;
};
export type TableData = {
    /** Styling for the table container, such as dimensions and alignment. */
    containerData?: PluginContainerData;
    /** Table dimensions. */
    dimensions?: TableData_Dimensions;
    /** Whether the table's first row is a heading. <br> Default: `false` */
    rowHeader?: boolean;
    /** Whether the table's first column is a heading. <br> Default: `false` */
    columnHeader?: boolean;
};
export type TableData_Dimensions = {
    colsWidthRatio?: number[];
    rowsHeight?: number[];
    colsMinWidth?: number[];
};
export type TableCellNode = {
    /**
     * Node type.
     *  Value: `TABLE_CELL`
     */
    type: 'TABLE_CELL';
    nodes: TableCellChildNode[];
    /** [Node ID](#node-ids). */
    id?: string;
    /** Table cell details. */
    tableCellData?: TableCellData;
};
/** Table cell content node. */
export type TableCellChildNode = ParagraphNode | HeadingNode | BulletedListNode | OrderedListNode | BlockquoteNode | AudioNode | FileNode | ImageNode | VideoNode | GifNode | DividerNode | CodeBlockNode | HtmlNode | LinkPreviewNode | AppEmbedNode | ButtonNode | EmbedNode;
export type TableCellData = {
    /** Styling for the cell, such as background color and text alignment. */
    cellStyle?: TableCellData_CellStyle;
    /** Cell border colors. */
    borderColors?: TableCellData_BorderColors;
};
export type TableCellData_CellStyle = {
    /**
     * Vertical alignment for the cell's text. Possible values:
     *  - `TOP`: Aligns the top padding edge of the cell with the top of the row.
     *  - `MIDDLE`: Centers the padding box of the cell in the row.
     *  - `BOTTOM`: Aligns the bottom padding edge of the cell with the bottom of the row.
     */
    verticalAlignment?: TableCellData_VerticalAlignment;
    /** Cell background color in a hexadecimal value, for example `#4287f5`. */
    backgroundColor?: string;
};
export type TableCellData_VerticalAlignment = 'TOP' | 'MIDDLE' | 'BOTTOM';
export declare const TableCellData_VerticalAlignment: {
    readonly TOP: "TOP";
    readonly MIDDLE: "MIDDLE";
    readonly BOTTOM: "BOTTOM";
};
export type TableCellData_BorderColors = {
    /** Left border color in a hexadecimal value. */
    left?: string;
    /** Right border color in a hexadecimal value. */
    right?: string;
    /** Top border color in a hexadecimal value. */
    top?: string;
    /** Bottom border color in a hexadecimal value. */
    bottom?: string;
};
/** A multimedia node that is used to embed and play video content directly in a page. When rendered, it is displayed as the video player with the specified video file. Users can interact with the controls to play, pause, rewind, and adjust the volume of the video. */
export type VideoNode = {
    /**
     * Node type.
     *  Value: `VIDEO`
     */
    type: 'VIDEO';
    /** Video details. */
    videoData: VideoData;
    /** [Node ID](#node-ids). */
    id?: string;
    nodes?: never[];
};
export type VideoData = {
    /** Video file details, such as source and dimensions. */
    video: Media;
    /** Styling for the video container, such as dimensions and alignment. */
    containerData?: PluginContainerData;
    /** Video thumbnail details, such as dimensions. */
    thumbnail?: Media;
    /**
     * Whether the video download button is disabled.
     *  Default: `false`
     */
    disableDownload?: boolean;
    /** Video title. */
    title?: string;
    /** Playback details. */
    options?: PlaybackOptions;
};
export type PlaybackOptions = {
    /** Whether the media automatically starts playing after opening a page. */
    autoPlay?: boolean;
    /** Whether the media is looped. */
    playInLoop?: boolean;
    /** Whether to show the media controls. */
    showControls?: boolean;
};
/** Represents nodes that can be added to the root level of `nodes` array. */
export type RootNode = ParagraphNode | HeadingNode | BulletedListNode | OrderedListNode | BlockquoteNode | CodeBlockNode | VideoNode | DividerNode | FileNode | GalleryNode | GifNode | HtmlNode | ImageNode | LinkPreviewNode | PollNode | AppEmbedNode | ButtonNode | CollapsibleListNode | TableNode | EmbedNode | AudioNode;
export declare const LATEST_VERSION = 1;
export type RicosDocumentNode = ParagraphNode | TextNode | HeadingNode | BulletedListNode | OrderedListNode | ListItemNode | BlockquoteNode | CodeBlockNode | VideoNode | DividerNode | FileNode | GalleryNode | GifNode | HtmlNode | ImageNode | LinkPreviewNode | PollNode | AppEmbedNode | ButtonNode | CollapsibleListNode | CollapsibleItemNode | CollapsibleItemTitleNode | CollapsibleItemBodyNode | TableNode | EmbedNode | TableCellNode | TableRowNode | AudioNode;
export type RicosDocumentNodeType = 'PARAGRAPH' | 'TEXT' | 'HEADING' | 'BULLETED_LIST' | 'ORDERED_LIST' | 'LIST_ITEM' | 'BLOCKQUOTE' | 'CODE_BLOCK' | 'VIDEO' | 'DIVIDER' | 'FILE' | 'GALLERY' | 'GIF' | 'HTML' | 'IMAGE' | 'LINK_PREVIEW' | 'POLL' | 'APP_EMBED' | 'BUTTON' | 'COLLAPSIBLE_LIST' | 'COLLAPSIBLE_ITEM' | 'COLLAPSIBLE_ITEM_TITLE' | 'COLLAPSIBLE_ITEM_BODY' | 'TABLE' | 'EMBED' | 'TABLE_CELL' | 'TABLE_ROW' | 'EXTERNAL' | 'AUDIO';
export declare const RicosDocumentNodeType: {
    readonly PARAGRAPH: "PARAGRAPH";
    readonly TEXT: "TEXT";
    readonly HEADING: "HEADING";
    readonly BULLETED_LIST: "BULLETED_LIST";
    readonly ORDERED_LIST: "ORDERED_LIST";
    readonly LIST_ITEM: "LIST_ITEM";
    readonly BLOCKQUOTE: "BLOCKQUOTE";
    readonly CODE_BLOCK: "CODE_BLOCK";
    readonly VIDEO: "VIDEO";
    readonly DIVIDER: "DIVIDER";
    readonly FILE: "FILE";
    readonly GALLERY: "GALLERY";
    readonly GIF: "GIF";
    readonly HTML: "HTML";
    readonly IMAGE: "IMAGE";
    readonly LINK_PREVIEW: "LINK_PREVIEW";
    readonly POLL: "POLL";
    readonly APP_EMBED: "APP_EMBED";
    readonly BUTTON: "BUTTON";
    readonly COLLAPSIBLE_LIST: "COLLAPSIBLE_LIST";
    readonly COLLAPSIBLE_ITEM: "COLLAPSIBLE_ITEM";
    readonly COLLAPSIBLE_ITEM_TITLE: "COLLAPSIBLE_ITEM_TITLE";
    readonly COLLAPSIBLE_ITEM_BODY: "COLLAPSIBLE_ITEM_BODY";
    readonly TABLE: "TABLE";
    readonly EMBED: "EMBED";
    readonly TABLE_CELL: "TABLE_CELL";
    readonly TABLE_ROW: "TABLE_ROW";
    readonly EXTERNAL: "EXTERNAL";
    readonly AUDIO: "AUDIO";
};
export type RichContent = RicosDocument;
export declare const RichContent: {
    fromJSON: (content: any) => RichContent;
    toJSON: (content: RichContent) => any;
};
export type Node_Type = RicosDocumentNodeType;
export declare const Node_Type: {
    readonly PARAGRAPH: "PARAGRAPH";
    readonly TEXT: "TEXT";
    readonly HEADING: "HEADING";
    readonly BULLETED_LIST: "BULLETED_LIST";
    readonly ORDERED_LIST: "ORDERED_LIST";
    readonly LIST_ITEM: "LIST_ITEM";
    readonly BLOCKQUOTE: "BLOCKQUOTE";
    readonly CODE_BLOCK: "CODE_BLOCK";
    readonly VIDEO: "VIDEO";
    readonly DIVIDER: "DIVIDER";
    readonly FILE: "FILE";
    readonly GALLERY: "GALLERY";
    readonly GIF: "GIF";
    readonly HTML: "HTML";
    readonly IMAGE: "IMAGE";
    readonly LINK_PREVIEW: "LINK_PREVIEW";
    readonly POLL: "POLL";
    readonly APP_EMBED: "APP_EMBED";
    readonly BUTTON: "BUTTON";
    readonly COLLAPSIBLE_LIST: "COLLAPSIBLE_LIST";
    readonly COLLAPSIBLE_ITEM: "COLLAPSIBLE_ITEM";
    readonly COLLAPSIBLE_ITEM_TITLE: "COLLAPSIBLE_ITEM_TITLE";
    readonly COLLAPSIBLE_ITEM_BODY: "COLLAPSIBLE_ITEM_BODY";
    readonly TABLE: "TABLE";
    readonly EMBED: "EMBED";
    readonly TABLE_CELL: "TABLE_CELL";
    readonly TABLE_ROW: "TABLE_ROW";
    readonly EXTERNAL: "EXTERNAL";
    readonly AUDIO: "AUDIO";
};
export type Node = RicosDocumentNode;
export declare namespace Node_Type {
    type PARAGRAPH = 'PARAGRAPH';
    type TEXT = 'TEXT';
    type HEADING = 'HEADING';
    type BULLETED_LIST = 'BULLETED_LIST';
    type ORDERED_LIST = 'ORDERED_LIST';
    type LIST_ITEM = 'LIST_ITEM';
    type BLOCKQUOTE = 'BLOCKQUOTE';
    type CODE_BLOCK = 'CODE_BLOCK';
    type VIDEO = 'VIDEO';
    type DIVIDER = 'DIVIDER';
    type FILE = 'FILE';
    type GALLERY = 'GALLERY';
    type GIF = 'GIF';
    type HTML = 'HTML';
    type IMAGE = 'IMAGE';
    type LINK_PREVIEW = 'LINK_PREVIEW';
    type POLL = 'POLL';
    type APP_EMBED = 'APP_EMBED';
    type BUTTON = 'BUTTON';
    type COLLAPSIBLE_LIST = 'COLLAPSIBLE_LIST';
    type COLLAPSIBLE_ITEM = 'COLLAPSIBLE_ITEM';
    type COLLAPSIBLE_ITEM_TITLE = 'COLLAPSIBLE_ITEM_TITLE';
    type COLLAPSIBLE_ITEM_BODY = 'COLLAPSIBLE_ITEM_BODY';
    type TABLE = 'TABLE';
    type EMBED = 'EMBED';
    type TABLE_CELL = 'TABLE_CELL';
    type TABLE_ROW = 'TABLE_ROW';
    type EXTERNAL = 'EXTERNAL';
    type AUDIO = 'AUDIO';
}
//# sourceMappingURL=ricos_document.d.ts.map