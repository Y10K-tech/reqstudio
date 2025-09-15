▌The direction i want to go into is outlined in the WORKPLAN.MD, also when you are implementing everything in the
▌WORKPLAN.MD keep in mind what has been outlined in in the REQSTUDIO-SEMANTIC-INDEX.md, you are not supposed to
▌implement ANYTHING from REQSTUDIO-SEMANTIC-INDEX.md. However, when you are following the instructions outline in
▌WORKPLAN.MD you need to essentially "pave the way" for when we do decided to implement everything that is outline in
▌REQSTUDION-SEMANTIC-INDEX.md. Do you get me?

Also, important color codes:
RGB color code: 219, 137, 200

This RGB color code is the color of the offiical logo of reqstudio

Also in the folder media, there is an image called:
reqstudio_logo.png. Use it
Also, there are a bunch of gifs from flaticon.com That perhaps would be interesting to use.
Adds some lively flair to reqstudio. Try to use all of them where apprioate, I've named them in such a way that the name should be as self-explanotory as possible (indicating what the animation looks like)

Extended Prompt: Modern PyQt6 Markdown Editor

I want the application to evolve from a bare-bones prototype into a modern, sleek, and beautiful desktop app. It should feel like a cross between:

The clean, aesthetic layouts of modern React websites

The powerful text manipulation features of Microsoft Word

The simplicity and speed of a Markdown editor

The result should be an app that is visually stunning, intuitive, fast, and extensible.

1. UI/UX & Visual Design

Inspiration: contemporary web dashboards and React apps. Think: Material Design, Tailwind-inspired styles, and minimal clutter.

Styling requirements:

Rounded corners, soft shadows, and smooth hover effects.

Polished typography hierarchy (headings, body, code).

A balanced, minimal color palette with accent highlights.

Light, Dark, and System theme support.

Layout:

Clear navigation with sidebars or tab bars.

Resizable panes (editor + preview side-by-side).

Status bar for file info, cursor position, and render mode.

Interactions:

Smooth animations (view switching, dialogs, expanding menus).

Keyboard shortcuts for all major actions (save, format, preview toggle).

Right-click context menus with formatting and styling actions.

2. Markdown Rendering (Full + Extended)

Baseline: support all official Markdown syntax out of the box (GitHub Flavored Markdown preferred).

Extended Features:

Syntax highlighting for code blocks (multi-language).

Math support via LaTeX/MathJax-style inline rendering ($E=mc^2$).

Inline checkboxes (- [x] Task).

Tables with borders and alternating row highlights.

Custom Syntax Extensions:

Text coloring via inline tags (e.g., {color:red}alert{/color}).

Text highlighting (e.g., {highlight:yellow}keyword{/highlight}).

Potential for other custom styles (underline, strikethrough, smallcaps).

3. Word-like Formatting Tools

Not every user knows Markdown. Add a toolbar + context menu for:

Bold, Italics, Underline

Headings (H1–H6)

Lists (ordered, unordered, checklists)

Links & images

Code & blockquote

Color picker for text (maps to custom Markdown syntax under the hood)

Highlight picker

Alignment (left, center, right, justified)

This ensures a WYSIWYG-like workflow for casual users while keeping Markdown as the core format.

4. Editor Features

Split-view editor: side-by-side Markdown + live preview.

Inline preview: headers, colors, and formatting visible in the editor.

Search & Replace: with regex option.

Auto-save + version history: recover past edits.

File handling: drag & drop, multi-tab editing.

Performance: fast rendering for large documents (10k+ lines).

5. Modern Enhancements & Polish

Theme customization: let users pick accent colors and font styles.

Snippets / Templates: insert common Markdown structures quickly.

Plugin system: so developers can extend with new formatting, syntax, or workflows.

Export options: PDF, DOCX, HTML, LaTeX.

Collaboration mode (future scope): optional real-time editing with other users.

Accessibility: keyboard navigation, high-contrast mode, screen reader support.

6. Performance & Technical Requirements

Built with PyQt6 using best practices (clean separation of logic and UI).

Rendering pipeline must be optimized (e.g., incremental re-rendering instead of full refresh).

Handle large Markdown files without lag.

Modular design for future maintainability and expansion.

7. Overall Vision

The application should feel like the next generation of Markdown editing tools:

Beautiful: polished UI inspired by React and Material design.

Practical: Markdown + Word-like controls so both power-users and casuals feel at home.

Powerful: extended Markdown features (coloring, math, tables).

Performant: optimized for speed and large documents.

Extensible: future-proof with plugins, themes, and exports.

👉 Goal: Deliver an editor that is not just a Markdown tool, but a delightful, modern writing experience, merging the elegance of web design with the robustness of desktop software.