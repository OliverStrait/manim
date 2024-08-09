from pygments.lexers import get_lexer_by_name

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
        pass
