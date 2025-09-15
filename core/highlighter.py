from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression


class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, document, srs_regex: str):
        super().__init__(document)
        self.rules = []

        # Headings (allow up to 3 leading spaces and optional space after #)
        fmt_h = QTextCharFormat()
        fmt_h.setFontWeight(QFont.Weight.Bold)
        self.rules.append((QRegularExpression(r"^\s{0,3}#{1,6}\s?.*$"), fmt_h))

        # Bold/italic markers
        fmt_b = QTextCharFormat()
        fmt_b.setFontWeight(QFont.Weight.Bold)
        self.rules.append((QRegularExpression(r"\*\*[^*]+\*\*"), fmt_b))

        fmt_i = QTextCharFormat()
        fmt_i.setFontItalic(True)
        self.rules.append((QRegularExpression(r"\*[^*\n]+\*"), fmt_i))

        # Code fences
        fmt_code = QTextCharFormat()
        fmt_code.setFontFamily("Monospace")
        fmt_code.setBackground(QColor("#f0f0f0"))
        self.rules.append((QRegularExpression(r"`[^`\n]+`"), fmt_code))

        # SRS-ID highlight
        fmt_id = QTextCharFormat()
        fmt_id.setForeground(QColor("#0066cc"))
        fmt_id.setFontWeight(QFont.Weight.Bold)
        self.rules.append((QRegularExpression(srs_regex), fmt_id))

        # Lists
        fmt_li = QTextCharFormat()
        fmt_li.setForeground(QColor("#444"))
        self.rules.append((QRegularExpression(r"^\s*[-*]\s+.*$"), fmt_li))

    def highlightBlock(self, text: str):
        for rx, fmt in self.rules:
            it = rx.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


class LivePreviewHighlighter(QSyntaxHighlighter):
    """
    Inline Markdown preview: render tokens while leaving source intact.
    - Hides/fades markdown markers except for token under caret.
    - Applies heading sizing/weight, bold/italic, inline code styling.
    Note: markers are visually de-emphasized (transparent) but still occupy space.
    """

    def __init__(self, document):
        super().__init__(document)
        self.caret_pos = -1
        # Marker style: faint and tiny so it minimally shifts layout
        self.fmt_marker = QTextCharFormat()
        self.fmt_marker.setForeground(QColor("#bbbbbb"))
        self.fmt_marker.setFontPointSize(1)

        self.fmt_bold = QTextCharFormat()
        self.fmt_bold.setFontWeight(QFont.Weight.Bold)

        self.fmt_italic = QTextCharFormat()
        self.fmt_italic.setFontItalic(True)

        self.fmt_code = QTextCharFormat()
        self.fmt_code.setFontFamily("Monospace")
        self.fmt_code.setBackground(QColor("#f0f0f0"))

        self.fmt_quote = QTextCharFormat()
        self.fmt_quote.setForeground(QColor("#666"))

        # Heading point sizes
        self.h_sizes = {1: 22, 2: 18, 3: 16, 4: 14, 5: 13, 6: 12}

    def setCaretPosition(self, pos: int):
        self.caret_pos = pos

    def _apply_heading(self, text: str, block_pos: int):
        rx = QRegularExpression(r"^(\s{0,3})(#{1,6})(\s?)(.*)$")
        m = rx.match(text)
        if not m.hasMatch():
            return
        indent, hashes, space, content = m.captured(1), m.captured(2), m.captured(3), m.captured(4)
        level = min(6, len(hashes))
        start_hash = len(indent)
        end_hash = start_hash + len(hashes) + (1 if space else 0)

        caret_in_block = self.caret_pos >= block_pos and self.caret_pos <= block_pos + len(text)
        caret_in_markers = caret_in_block and (block_pos + start_hash <= self.caret_pos < block_pos + end_hash)

        if not caret_in_markers:
            # De-emphasize markers
            self.setFormat(start_hash, end_hash - start_hash, self.fmt_marker)

        # Style content
        content_start = end_hash
        if content:
            fmt = QTextCharFormat()
            fmt.setFontWeight(QFont.Weight.Bold)
            fmt.setFontPointSize(self.h_sizes.get(level, 14))
            self.setFormat(content_start, max(0, len(text) - content_start), fmt)

    def _apply_emphasis(self, text: str, block_pos: int):
        # Bold **text**
        rx_bold = QRegularExpression(r"\*\*([^*].*?)\*\*")
        it = rx_bold.globalMatch(text)
        while it.hasNext():
            m = it.next()
            a, b = m.capturedStart(), m.capturedEnd()
            caret_in = block_pos + a <= self.caret_pos <= block_pos + b
            if not caret_in:
                self.setFormat(a, 2, self.fmt_marker)
                self.setFormat(b - 2, 2, self.fmt_marker)
            inner_start = m.capturedStart(1)
            inner_len = m.capturedLength(1)
            self.setFormat(inner_start, inner_len, self.fmt_bold)

        # Italic *text*
        rx_italic = QRegularExpression(r"(?<!\*)\*([^*\n].*?)\*(?!\*)")
        it = rx_italic.globalMatch(text)
        while it.hasNext():
            m = it.next()
            a, b = m.capturedStart(), m.capturedEnd()
            caret_in = block_pos + a <= self.caret_pos <= block_pos + b
            if not caret_in:
                self.setFormat(a, 1, self.fmt_marker)
                self.setFormat(b - 1, 1, self.fmt_marker)
            inner_start = m.capturedStart(1)
            inner_len = m.capturedLength(1)
            self.setFormat(inner_start, inner_len, self.fmt_italic)

        # Inline code `code`
        rx_code = QRegularExpression(r"`([^`\n]+)`")
        it = rx_code.globalMatch(text)
        while it.hasNext():
            m = it.next()
            a, b = m.capturedStart(), m.capturedEnd()
            caret_in = block_pos + a <= self.caret_pos <= block_pos + b
            if not caret_in:
                self.setFormat(a, 1, self.fmt_marker)
                self.setFormat(b - 1, 1, self.fmt_marker)
            inner_start = m.capturedStart(1)
            inner_len = m.capturedLength(1)
            self.setFormat(inner_start, inner_len, self.fmt_code)

    def highlightBlock(self, text: str):
        block_pos = self.currentBlock().position()
        # Code fences (multi-line)
        state = self.previousBlockState()
        in_fence = state == 1
        fence_rx = QRegularExpression(r"^\s*```")
        if in_fence:
            # Style whole line as code
            self.setFormat(0, len(text), self.fmt_code)
            # Closing fence?
            if fence_rx.match(text).hasMatch():
                # Hide/soften fence markers if caret not inside
                if not (block_pos <= self.caret_pos < block_pos + len(text)):
                    self.setFormat(0, len(text), self.fmt_code)
                self.setCurrentBlockState(0)
            else:
                self.setCurrentBlockState(1)
            return
        else:
            # Opening fence
            if fence_rx.match(text).hasMatch():
                # Soften fence line and switch to fence state
                self.setFormat(0, len(text), self.fmt_code)
                self.setCurrentBlockState(1)
                return
            else:
                self.setCurrentBlockState(0)

        # Single-line constructs
        self._apply_heading(text, block_pos)
        self._apply_lists(text, block_pos)
        self._apply_blockquote(text, block_pos)
        self._apply_emphasis(text, block_pos)

    def _apply_lists(self, text: str, block_pos: int):
        # Unordered: - or *
        rx_ul = QRegularExpression(r"^(\s{0,3})([-*])\s+(.*)$")
        m = rx_ul.match(text)
        if m.hasMatch():
            indent, marker, rest = m.captured(1), m.captured(2), m.captured(3)
            start = len(indent)
            end = start + 2  # 'x '
            caret_in_markers = block_pos + start <= self.caret_pos < block_pos + end
            if not caret_in_markers:
                self.setFormat(start, end - start, self.fmt_marker)
            return
        # Ordered: 1. or 1)
        rx_ol = QRegularExpression(r"^(\s{0,3})(\d+)[\.)]\s+(.*)$")
        m = rx_ol.match(text)
        if m.hasMatch():
            indent, digits = m.captured(1), m.captured(2)
            start = len(indent)
            end = start + len(digits) + 2
            caret_in_markers = block_pos + start <= self.caret_pos < block_pos + end
            if not caret_in_markers:
                self.setFormat(start, end - start, self.fmt_marker)
            return

    def _apply_blockquote(self, text: str, block_pos: int):
        rx = QRegularExpression(r"^(\s{0,3})(>)\s?(.*)$")
        m = rx.match(text)
        if not m.hasMatch():
            return
        indent, gt, rest = m.captured(1), m.captured(2), m.captured(3)
        start = len(indent)
        end = start + 1 + (1 if text[start+1:start+2] == ' ' else 0)
        caret_in_markers = block_pos + start <= self.caret_pos < block_pos + end
        if not caret_in_markers:
            self.setFormat(start, end - start, self.fmt_marker)
        if rest:
            self.setFormat(end, max(0, len(text) - end), self.fmt_quote)
