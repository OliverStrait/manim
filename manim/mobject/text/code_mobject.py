"""Mobject representing highlighted source code listings."""

from __future__ import annotations

__all__ = [
    "Code",
]

import os
from pathlib import Path

from pygments import highlight, styles
from pygments.formatter import Formatter
from pygments.lexers import get_lexer_by_name, guess_lexer, guess_lexer_for_filename
from pygments.token import Token

# from pygments.styles import get_all_styles
from manim.constants import *
from manim.mobject.geometry.arc import Dot
from manim.mobject.geometry.polygram import RoundedRectangle
from manim.mobject.geometry.shape_matchers import SurroundingRectangle
from manim.mobject.text.text_mobject import Paragraph
from manim.mobject.types.vectorized_mobject import VGroup
from manim.utils.color import WHITE


class DataFormatter(Formatter):
    def __init__(self, **options):
        super().__init__(self, **options)

        self.indentation = options.get("indentation", "    ")

        self.styles = {}
        self.bg_color = self.style.background_color
        self.default_color = self.opposite_color(self.bg_color)
        for token, style in self.style:
            value = style["color"]
            if not value:
                value = self.default_color
            self.styles[token] = value

    def format(self, tokensource, outfile):
        self.mapping = [[]]
        self.ident_spaces = [0]
        """counting of identations spaces"""
        lastval = ""
        lasttype = None

        for token_type, value in tokensource:
            value: str

            print((token_type, value, self.styles.get(token_type, "None")))
            if token_type not in self.styles:
                # Token types which are not found in style mapping
                token_type = token_type.parent
                # eg: parent of Token.Literal.String.Double is
                # Token.Literal.String

            if lastval == "\n":
                outfile.write("<new_line>\n")
                self.mapping.append([])
                self.ident_spaces.append(0)
                lastval = value
                lasttype = token_type

            elif token_type == lasttype or value == " ":
                # join same tokens and empty spaces to sam string block
                lastval += value

            elif lasttype == Token.Text:
                # spaces = value.count(" ")
                # self.ident_spaces[-1] += spaces % len(self.indentation)
                lasttype = token_type
                lastval += value
            else:
                if lastval:
                    stylet = self.styles[lasttype]
                    self.mapping[-1].append((lastval, "#" + stylet))

                lastval = value
                lasttype = token_type

        # if something is left in the buffer, write it to the
        # output file, then close the opened <pre> tag
        # print(self.mapping, "\n", self.ident_spaces)
        print("background", self.bg_color)

    def highlight_code(self, code, lexer):
        highlight(
            code,
            lexer,
            self,
        )

    def get_mapping(self):
        return self.mapping

    def get_identation(self):
        return self.ident_spaces

    def get_bg_and_def_color(self):
        return self.bg_color, self.default_color

    @staticmethod
    def opposite_color(color: str) -> str:
        """Generate opposite color string"""
        if color == "#000000":
            return "#ffffff"
        elif color == "#ffffff":
            return "#000000"
        else:
            new_hexes = []

            for i in range(1, 6, 2):
                hex_str = color[i : i + 2]

                hex_int = int(hex_str, 16)
                new_hex = hex(abs(hex_int - 255)).strip("0x")
                new_hex = new_hex if len(new_hex) > 1 else "0" + new_hex
                new_hexes.append(new_hex)
            return "#" + "".join(new_hexes)


def _search_file_path(path_name: Path | str):
    """Function to validate file."""
    # TODO Hard coded directories
    possible_paths = [
        Path() / "assets" / "codes" / path_name,
        Path(path_name).expanduser(),
    ]

    for path in possible_paths:
        if path.exists():
            return path
    else:
        error = (
            f"From: {Path.cwd()}, could not find {path_name} at either "
            + f"of these locations: {list(map(str, possible_paths))}"
        )
        raise OSError(error)


DEFAULT_STYLE = "vim"


class Code(VGroup):
    """A highlighted source code listing.

    An object ``listing`` of :class:`.Code` is a :class:`.VGroup` consisting
    of three objects:

    - The background, ``listing.background_mobject``. This is either
      a :class:`.Rectangle` (if the listing has been initialized with
      ``background="rectangle"``, the default option) or a :class:`.VGroup`
      resembling a window (if ``background="window"`` has been passed).

    - The line numbers, ``listing.line_numbers`` (a :class:`.Paragraph`
      object).

    - The highlighted code itself, ``listing.code`` (a :class:`.Paragraph`
      object).

    .. WARNING::

        Using a :class:`.Transform` on text with leading whitespace (and in
        this particular case: code) can look
        `weird <https://github.com/3b1b/manim/issues/1067>`_. Consider using
        :meth:`remove_invisible_chars` to resolve this issue.

    Examples
    --------

    Normal usage::

        listing = Code(
            "helloworldcpp.cpp",
            tab_width=4,
            background_stroke_width=1,
            background_stroke_color=WHITE,
            insert_line_no=True,
            style=Code.styles_list[15],
            background="window",
            language="cpp",
        )

    We can also render code passed as a string (but note that
    the language has to be specified in this case):

    .. manim:: CodeFromString
        :save_last_frame:

        class CodeFromString(Scene):
            def construct(self):
                code = '''from manim import Scene, Square

        class FadeInSquare(Scene):
            def construct(self):
                s = Square()
                self.play(FadeIn(s))
                self.play(s.animate.scale(2))
                self.wait()
        '''
                rendered_code = Code(code=code, tab_width=4, background="window",
                                    language="Python", font="Monospace")
                self.add(rendered_code)

    Parameters
    ----------
    file_name
        Name of the code file to display.
    code
        If ``file_name`` is not specified, a code string can be
        passed directly.
    tab_width
        Number of space characters corresponding to a tab character. Defaults to 3.
    line_spacing
        Amount of space between lines in relation to font size. Defaults to 0.3, which means 30% of font size.
    font_size
        A number which scales displayed code. Defaults to 24.
    font
        The name of the text font to be used. Defaults to ``"Monospace"``.
        This is either a system font or one loaded with `text.register_font()`. Note
        that font family names may be different across operating systems.
    stroke_width
        Stroke width for text. 0 is recommended, and the default.
    margin
        Inner margin of text from the background. Defaults to 0.3.
    indentation_chars
        "Indentation chars" refers to the spaces/tabs at the beginning of a given code line. Defaults to ``"    "`` (spaces).
    background
        Defines the background's type. Currently supports only ``"rectangle"`` (default) and ``"window"``.
    background_stroke_width
        Defines the stroke width of the background. Defaults to 1.
    background_stroke_color
        Defines the stroke color for the background. Defaults to ``WHITE``.
    corner_radius
        Defines the corner radius for the background. Defaults to 0.2.
    insert_line_no
        Defines whether line numbers should be inserted in displayed code. Defaults to ``True``.
    line_no_from
        Defines the first line's number in the line count. Defaults to 1.
    line_no_buff
        Defines the spacing between line numbers and displayed code. Defaults to 0.4.
    style
        Defines the style type of displayed code. You can see possible names of styles in with :attr:`styles_list`. Defaults to ``"vim"``.
    language
        Specifies the programming language the given code was written in. If ``None``
        (the default), the language will be automatically detected. For the list of
        possible options, visit https://pygments.org/docs/lexers/ and look for
        'aliases or short names'.
    generate_html_file
        Defines whether to generate highlighted html code to the folder `assets/codes/generated_html_files`. Defaults to `False`.
    warn_missing_font
        If True (default), Manim will issue a warning if the font does not exist in the
        (case-sensitive) list of fonts returned from `manimpango.list_fonts()`.

    Attributes
    ----------
    background_mobject : :class:`~.VGroup`
        The background of the code listing.
    line_numbers : :class:`~.Paragraph`
        The line numbers for the code listing. Empty, if
        ``insert_line_no=False`` has been specified.
    code : :class:`~.Paragraph`
        The highlighted code.

    """

    # tuples in the form (name, aliases, filetypes, mimetypes)
    # 'language' is aliases or short names
    # For more information about pygments.lexers visit https://pygments.org/docs/lexers/

    _styles_list_cache = None
    # For more information about pygments.styles visit https://pygments.org/docs/styles/

    def __init__(
        self,
        file_name: str | os.PathLike | None = None,
        code: str | None = None,
        language: str | None = None,
        tab_width: int = 3,
        line_spacing: float = 0.6,
        font_size: float = 24,
        font: str = "Monospace",  # This should be in the font list on all platforms.
        stroke_width: float = 0,
        margin: float = 0.3,
        indentation_chars: str = "    ",
        background: str = "rectangle",
        background_stroke_width: float = 1,
        background_stroke_color: str = WHITE,
        corner_radius: float = 0.2,
        insert_line_no: bool = True,
        line_no_from: int = 1,
        line_no_buff: float = 0.4,
        style: str = DEFAULT_STYLE,
        generate_html_file: bool = False,
        warn_missing_font: bool = True,
        **kwargs,
    ):
        if generate_html_file:
            print(
                f"at:{Code.__name__} argument 'generate_html_file' is deprecated and does not work anymore"
            )

        create_line_numbers = insert_line_no
        if isinstance(style, str):
            style = style.lower()
            if not self.validate_style(style):
                print(
                    f'{Code.__name__}: style "{style}" is not supported, using default style: "{DEFAULT_STYLE}" '
                )
                style = DEFAULT_STYLE

        if file_name:
            assert isinstance(file_name, str)
            file_path = _search_file_path(file_name)
            code_string = file_path.read_text(encoding="utf-8")
            lexer = guess_lexer_for_filename(file_path, code_string)

        elif isinstance(code, str):
            code_string = code
            file_path = None
            if language is not None:
                lexer = get_lexer_by_name(language, **{})
            else:
                lexer = guess_lexer(code_string)

        else:
            raise ValueError(
                "Neither a code file nor a code string have been specified. Cannot generate Code block",
            )

        formatter = DataFormatter(
            style=style, linenos=False, indentation=indentation_chars
        )
        formatter.highlight_code(code_string, lexer)
        mapping = formatter.get_mapping()
        bg_color, default_color = formatter.get_bg_and_def_color()
        tabs = formatter.get_identation()
        tabs = [0 for a in tabs]
        print(tabs)
        print(mapping)
        # print("new map",mapping)
        # tabs = [spaces % len(indentation_chars) for spaces in indents]

        code_text = ColoredCodeText(
            stroke_width,
            mapping,
            tabs,
            line_spacing,
            tab_width,
            font_size,
            font,
            warn_missing_font,
        )

        if create_line_numbers:
            line_numbers: Paragraph = LineNumbers(
                mapping,
                default_color,
                stroke_width,
                line_no_from,
                line_spacing,
                font_size,
                font,
                warn_missing_font,
            )

            line_numbers.next_to(code_text, direction=LEFT, buff=line_no_buff)
            foreground = VGroup(code_text, line_numbers)
        else:
            foreground = code_text

        bg_function = Neutral if background == "rectangle" else Mac_os

        background_mobject = bg_function(
            foreground,
            margin,
            bg_color,
            background_stroke_width,
            background_stroke_color,
            corner_radius,
        )

        return super().__init__(
            background_mobject,
            foreground,
            stroke_width=stroke_width,
            **kwargs,
        )

    @classmethod
    def get_styles_list(cls) -> list[str]:
        """Return a list of available code styles.
        For more information about pygments.styles visit https://pygments.org/docs/styles/
        """
        if cls._styles_list_cache is None:
            cls._styles_list_cache = list(styles.get_all_styles())
        return cls._styles_list_cache

    @classmethod
    def validate_style(cls, style: str) -> bool:
        return style in cls.get_styles_list()


# Mobject constructors:


def LineNumbers(
    text_mapping: list[list[str, str]],
    default_color,
    line_width,
    starting_line,
    line_spacing,
    font_size,
    font,
    warn_missing_font,
) -> Paragraph:
    """Function to generate line_numbers.

    Returns
    -------
    :class:`~.Paragraph`
        The generated line_numbers according to parameters.
    """
    line_numbers_array = []
    for line_no in range(starting_line, len(text_mapping) + starting_line):
        line_numbers_array.append(str(line_no))

    line_numbers: Paragraph = Paragraph(
        *line_numbers_array,
        line_spacing=line_spacing,
        alignment="right",
        font_size=font_size,
        font=font,
        disable_ligatures=True,
        stroke_width=line_width,
        warn_missing_font=warn_missing_font,
    )
    for i in line_numbers:
        i.set_color(default_color)

    return line_numbers


def ColoredCodeText(
    line_width,
    text_mapping: list[list[str, str]],
    tabs: list[int],
    line_spacing,
    tab_width,
    font_size,
    font,
    warn_missing_font=False,
):
    """Function to generate code.

    Returns
    -------
    :class:`~.Paragraph`
        The generated code according to parameters.
    """
    lines_text = []

    for tab_count, line in zip(tabs, text_mapping):
        line_str = ""
        for word in line:
            line_str += word[0]
        lines_text.append(("\t" * tab_count) + line_str)

    code = Paragraph(
        *list(lines_text),
        line_spacing=line_spacing,
        tab_width=tab_width,
        font_size=font_size,
        font=font,
        disable_ligatures=True,
        stroke_width=line_width,
        warn_missing_font=warn_missing_font,
    )

    for line_no in range(code.__len__()):
        line = code.chars[line_no]
        line_char_index = tabs[line_no]
        for word_index in range(text_mapping[line_no].__len__()):
            line[
                line_char_index : line_char_index
                + text_mapping[line_no][word_index][0].__len__()
            ].set_color(text_mapping[line_no][word_index][1])
            line_char_index += text_mapping[line_no][word_index][0].__len__()
    return code


# Background box constructors:


def Neutral(
    foreground: VGroup | Paragraph,
    margin,
    bg_col,
    bg_stroke_width,
    bg_stroke_color,
    corner_radius,
) -> SurroundingRectangle:
    rect = SurroundingRectangle(
        foreground,
        buff=margin,
        color=bg_col,
        fill_color=bg_col,
        stroke_width=bg_stroke_width,
        stroke_color=bg_stroke_color,
        fill_opacity=1,
    )
    rect.round_corners(corner_radius)
    return rect


def Mac_os(
    foreground: VGroup | Paragraph,
    margin,
    bg_col,
    bg_stroke_width,
    bg_stroke_color,
    corner_radius,
) -> VGroup:
    height = foreground.height + 0.1 * 3 + 2 * margin
    width = foreground.width + 0.1 * 3 + 2 * margin

    rect = RoundedRectangle(
        corner_radius=corner_radius,
        height=height,
        width=width,
        stroke_width=bg_stroke_width,
        stroke_color=bg_stroke_color,
        color=bg_col,
        fill_opacity=1,
    )
    red_button = Dot(radius=0.1, stroke_width=0, color="#ff5f56")
    red_button.shift(LEFT * 0.1 * 3)
    yellow_button = Dot(radius=0.1, stroke_width=0, color="#ffbd2e")
    green_button = Dot(radius=0.1, stroke_width=0, color="#27c93f")
    green_button.shift(RIGHT * 0.1 * 3)
    buttons = VGroup(red_button, yellow_button, green_button)
    buttons.shift(
        UP * (height / 2 - 0.1 * 2 - 0.05)
        + LEFT * (width / 2 - 0.1 * 5 - corner_radius / 2 - 0.05),
    )

    window = VGroup(rect, buttons)
    x = (height - foreground.height) / 2 - 0.1 * 3
    window.shift(foreground.get_center())
    window.shift(UP * x)
    return window
