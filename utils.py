import re
from notion_client import Client

def extract_title_from_markdown(text):
    """
    Extract title from the first # heading in markdown text.

    Args:
        text: Markdown text containing headings

    Returns:
        The title string without # symbols, or None if no heading found
    """
    lines = text.split('\n')

    for line in lines:
        if line.strip().startswith('#'):
            # Remove the # symbols and strip whitespace
            title = re.sub(r'^#+\s*', '', line).strip()
            return title

    return None


def extract_section(text, section_name):
    """
    Extract content from a specific markdown section by heading name.

    Args:
        text: Markdown text with sections
        section_name: Name of the section to extract (e.g., 'Title', 'Abstract')

    Returns:
        Content of the section without the heading, or None if section not found
    """
    lines = text.split('\n')
    section_content = []
    in_section = False

    for line in lines:
        stripped = line.strip()

        # Check if we found the section heading
        if re.match(rf'^#+\s*{re.escape(section_name)}\s*$', stripped, re.IGNORECASE):
            in_section = True
            continue

        # If we're in the section and hit another heading, we're done
        if in_section and stripped and stripped[0] == '#':
            break

        # Collect content from the section
        if in_section and stripped:
            section_content.append(line)

    return '\n'.join(section_content).strip() if section_content else None


def chunk_content(content, chunk_size=2000):
    """
    Split content into chunks of max chunk_size characters, breaking at word boundaries.

    Args:
        content: String content to chunk
        chunk_size: Maximum characters per chunk (default 2000)

    Returns:
        List of content chunks
    """
    chunks = []
    while len(content) > 0:
        if len(content) <= chunk_size:
            chunks.append(content)
            break

        # Find the last space before chunk_size to avoid breaking words
        chunk_end = chunk_size
        last_space = content.rfind(' ', 0, chunk_size)

        if last_space > 0:
            chunk_end = last_space

        chunks.append(content[:chunk_end].strip())
        content = content[chunk_end:].strip()

    return chunks


def markdown_to_notion_blocks(markdown_text):
    """
    Convert markdown text to Notion block structure.

    Args:
        markdown_text: Markdown formatted text

    Returns:
        List of Notion block dictionaries
    """
    blocks = []
    lines = markdown_text.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            i += 1
            continue

        # Headings
        if stripped.startswith('### '):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": stripped[4:].strip()}}]
                }
            })
        elif stripped.startswith('## '):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": stripped[3:].strip()}}]
                }
            })
        elif stripped.startswith('# '):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": stripped[2:].strip()}}]
                }
            })
        # Bullet lists
        elif stripped.startswith('- '):
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": stripped[2:].strip()}}]
                }
            })
        # Numbered lists
        elif re.match(r'^\d+\.\s', stripped):
            content = re.sub(r'^\d+\.\s', '', stripped)
            blocks.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": content.strip()}}]
                }
            })
        # Code blocks
        elif stripped.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            blocks.append({
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{"type": "text", "text": {"content": '\n'.join(code_lines)}}],
                    "language": "text"
                }
            })
        # Regular paragraphs with formatting
        else:
            rich_text = parse_inline_markdown(stripped)
            if rich_text:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": rich_text
                    }
                })

        i += 1

    return blocks


def parse_inline_markdown(text):
    """
    Parse inline markdown formatting (bold, italic, strikethrough) and return rich text.

    Args:
        text: Text with inline markdown

    Returns:
        List of rich text objects
    """
    rich_text = []
    pattern = r'\*\*(.+?)\*\*|__(.+?)__|~~(.+?)~~|_(.+?)_|\*(.+?)\*'
    last_end = 0

    for match in re.finditer(pattern, text):
        # Add plain text before match
        if match.start() > last_end:
            rich_text.append({
                "type": "text",
                "text": {"content": text[last_end:match.start()]}
            })

        # Determine formatting type
        if match.group(1):  # **bold**
            rich_text.append({
                "type": "text",
                "text": {"content": match.group(1)},
                "annotations": {"bold": True}
            })
        elif match.group(2):  # __bold__
            rich_text.append({
                "type": "text",
                "text": {"content": match.group(2)},
                "annotations": {"bold": True}
            })
        elif match.group(3):  # ~~strikethrough~~
            rich_text.append({
                "type": "text",
                "text": {"content": match.group(3)},
                "annotations": {"strikethrough": True}
            })
        elif match.group(4):  # _italic_
            rich_text.append({
                "type": "text",
                "text": {"content": match.group(4)},
                "annotations": {"italic": True}
            })
        elif match.group(5):  # *italic*
            rich_text.append({
                "type": "text",
                "text": {"content": match.group(5)},
                "annotations": {"italic": True}
            })

        last_end = match.end()

    # Add remaining plain text
    if last_end < len(text):
        rich_text.append({
            "type": "text",
            "text": {"content": text[last_end:]}
        })

    return rich_text if rich_text else [{"type": "text", "text": {"content": text}}]


def add_content_to_page(notion_token, page_id, content):
    """
    Add markdown content to a Notion page, converting it to appropriate blocks.

    Args:
        notion_token: Notion API token
        page_id: ID of the page to add content to
        content: Markdown formatted content to add
    """
    notion = Client(auth=notion_token)
    blocks = markdown_to_notion_blocks(content)

    # Add blocks in chunks to respect API limits
    chunk_size = 100
    for i in range(0, len(blocks), chunk_size):
        notion.blocks.children.append(
            block_id=page_id,
            children=blocks[i:i + chunk_size]
        )


def write_to_notion(title, url, content, notion_token, database_id):
    """
    Write JSON output (Summary, Extended Summary) to a Notion database page.

    Args:
        title: Document title
        url: Document URL
        content: Content to add to the page (will be chunked if needed)
        notion_token: Your Notion API token
        database_id: The ID of your database
    """

    # Initialize the Notion client
    notion = Client(auth=notion_token)

    # Create a new page in the database
    new_page = notion.pages.create(
        parent={"database_id": database_id},
        properties={
            "Title": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            },
            "URL": {
                "url": url
            }
        }
    )

    # Add content to the page if provided
    if content:
        add_content_to_page(notion_token, new_page['id'], content)

    return new_page