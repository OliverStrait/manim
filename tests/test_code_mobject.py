from pygments.lexers import get_lexer_by_name

from manim.mobject.text.code_mobject import (
    ColoredCodeText,
    _find_colors,
    _generate_color_to_text_mapping,
    _generate_html_code_block,
    opposite_color,
)
from manim.mobject.text.text_mobject import Paragraph

IDENTATION_CHAR = "    "
CODE_1 = """\
def test()
    print("Hi")
    for i in out:
        print(i, "see you")
"""
lexer_python = get_lexer_by_name(_alias="python", **{})
mapping = []
tabs = []
html = ""


class TestInternals:
    def test_code_indentation_n_rows(self):
        global mapping, tabs, html
        html = _generate_html_code_block(code=CODE_1, style="vim", lexer=lexer_python)
        mapping, tabs = _generate_color_to_text_mapping(
            "#000000", html, ident_char=IDENTATION_CHAR
        )
        print("mapping:", mapping, "\ntabs: ", tabs)
        assert tabs[0] == 0
        assert tabs[1] == 1
        assert tabs[3] == 2
        assert len(mapping) == 4
        assert len(mapping) == len(tabs)

    def test_create_colored_code(self):
        colored_code = ColoredCodeText(1, mapping, tabs, 0.5, 4, 24, font="Monospace")
        assert isinstance(colored_code, Paragraph)
        assert len(colored_code.chars) == 4
        # assert False

    def test_color(self):
        print("opposite:", opposite_color("#000000"))

        bg_col, default_col = _find_colors(html)
        assert bool(bg_col == "#000000" and default_col == "#ffffff")
        assert opposite_color("#ffffff") == "#000000"
        assert opposite_color("#fefdfc") == "#010203"
        assert opposite_color("#010203") == "#fefdfc"
