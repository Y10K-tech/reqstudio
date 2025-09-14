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
