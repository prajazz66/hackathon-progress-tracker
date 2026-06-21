# File Attachment Feature

## Overview

A new file attachment feature has been added to the Hackathon Progress Tracker, allowing users to upload, view, modify, and remove `.md` (Markdown) and `.pdf` files for each hackathon entry.

## Feature Details

### Upload
- Users can upload `.md` or `.pdf` files via the file upload button in the description tile
- PDF files larger than 500KB are automatically compressed using gzip to save storage space
- All files are stored in `static/uploads/` directory with UUID-based filenames for security
- Original filenames are preserved in the database for display purposes

### View
- `.md` files open in a read-only view mode at `/view_file/<filename>`
- Markdown content is automatically converted to HTML with syntax highlighting support
- `.pdf` files open in the browser's built-in PDF viewer

### Modify (Markdown only)
- `.md` files can be edited in-place via the Edit button
- Opens an editing interface at `/modify_file/<hackathon_id>/<filename>`
- Changes are saved directly to the file

### Delete
- Files can be removed via the X button next to each attachment
- Deleting a file removes both the file from disk and the reference from the database
- Files are automatically cleaned up when a hackathon is deleted

## File Structure

```
hackathon-progress-tracker/
├── app.py                    # Updated with file routes
├── hackathons.json           # Data file (now includes file_attachments array)
├── static/
│   └── uploads/              # File storage directory
├── templates/
│   ├── dashboard.html        # Updated with file UI
│   ├── view_md.html          # Markdown viewer template
│   └── edit_md.html          # Markdown editor template
└── FEATURE_FILE_ATTACHMENT.md # This documentation
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload_file/<hackathon_id>` | POST | Upload .md or .pdf file |
| `/view_file/<filename>` | GET | View the file (md renders as HTML, pdf in browser) |
| `/modify_file/<hackathon_id>/<filename>` | GET | Edit markdown file inline |
| `/save_md_file/<hackathon_id>/<filename>` | POST | Save edited markdown content |
| `/delete_file/<hackathon_id>/<filename>` | POST | Remove file attachment |

## Storage Strategy

- Files are stored locally in `static/uploads/` directory
- Original filenames are stored in the JSON database alongside hackathon data
- Large PDFs (>500KB) are gzip-compressed to optimize storage
- Each file gets a unique UUID-based name to prevent conflicts and security issues

## Theme Consistency

The file attachment UI follows the existing dark theme:
- Background: `#151515` / `#222` tiles
- Text: `#ddd` / `#888` / `#666` hierarchy
- Borders: `#333` with `#222` accents
- Buttons: `#222` background with uppercase text
- Hover states: Darken borders and lighten text

## Usage Workflow

1. **Add a hackathon** - Use the form at the top of the dashboard
2. **Upload file** - Click "Upload .md/.pdf" in the description tile of any hackathon
3. **View file** - Click on the filename to view it in read mode
4. **Edit file** - For `.md` files, click "Edit" to modify the content
5. **Remove file** - Click "X" to delete the attachment

## Notes

- Authentication is required for all file operations (uses existing 'oneshot' passcode)
- Only `.md` and `.pdf` file types are allowed
- Maximum file size is 10MB
- This feature does not modify any existing functionality - all other features remain unchanged