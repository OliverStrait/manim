"""Mobject representing highlighted source code listings."""

from __future__ import annotations

__all__ = [
    "Code",
]

import html
import os
import re
from pathlib import Path

from pygments import highlight, styles
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer, guess_lexer_for_filename

# from pygments.styles import get_all_styles
from manim.constants import *
from manim.mobject.geometry.arc import Dot
from manim.mobject.geometry.polygram import RoundedRectangle
from manim.mobject.geometry.shape_matchers import SurroundingRectangle
from manim.mobject.text.text_mobject import Paragraph
from manim.mobject.types.vectorized_mobject import VGroup
from manim.utils.color import WHITE

DEFAULT_STYLE = "vim"


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
        tab_width: int = 3,
        line_spacing: float = 0.6,
        font_size: float = 24,
        font: str = "Monospace",  # This should be in the font list on all platforms.
        stroke_width: float = 0,
        margin: float = 0.3,
        indentation_chars: str = "    ",
        background: str = "rectangle",  # or window
        background_stroke_width: float = 1,
        background_stroke_color: str = WHITE,
        corner_radius: float = 0.2,
        insert_line_no: bool = True,
        line_no_from: int = 1,
        line_no_buff: float = 0.4,
        style: str = DEFAULT_STYLE,
        language: str | None = None,
        generate_html_file: bool = False,
        warn_missing_font: bool = True,
        **kwargs,
    ):
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
                "Neither a code file nor a code string have been specified. Cannot generate Code Block",
            )

        html_code_block = _generate_html_code_block(code_string, style, lexer)

        bg_color, default_color = _find_colors(html_code_block)

        mapping, tabs = _generate_color_to_text_mapping(
            default_color, html_code_block, indentation_chars
        )

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

        super().__init__(
            background_mobject,
            foreground,
            stroke_width=stroke_width,
            **kwargs,
        )

        if generate_html_file:
            if create_line_numbers:
                html_code_block = _insert_line_numbers_in_html(
                    html_code_block, create_line_numbers, mapping, default_color
                )

            # TODO Hard coded directories
            output_folder = Path() / "assets" / "codes" / "generated_html_files"
            print(f"Code_generation: html_ output: {output_folder}")
            output_folder.mkdir(parents=True, exist_ok=True)
            if file_name is None:
                file_name = style + str(
                    len(code_string)
                )  # TODO This one is very hacky and not that informatic
            (output_folder / f"{file_name}.html").write_text(html_code_block)

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


def _generate_color_to_text_mapping(default_color, html_string: str, ident_char):
    """Function to background_color, generate code_json and tab_spaces from html_string.
    background_color is just background color of displayed code.
    code_json is 2d array with rows as line numbers
    and columns as a array with length 2 having text and text's color value.
    tab_spaces is 2d array with rows as line numbers
    and columns as corresponding number of indentation_chars in front of that line in code.
    """

    def preparse_html_string() -> list[str]:
        nonlocal html_string
        for i in range(3, -1, -1):
            html_string = html_string.replace("</" + " " * i, "</")

        for i in range(10, -1, -1):
            html_string = html_string.replace(
                "</span>" + " " * i,
                " " * i + "</span>",
            )
        html_string = html_string.replace("background-color:", "background:")

        line_numbers = html_string.find(
            "</td><td><pre"
        )  # starting point if line_numbers:
        if line_numbers > -1:
            start_point = line_numbers + 9
        else:
            start_point = html_string.find("<pre")

        html_string = html_string[start_point:]

        lines = html_string.split("\n")

        lines = lines[0 : len(lines) - 2]
        start_point = lines[0].find(">")
        lines[0] = lines[0][start_point + 1 :]

        return lines

    tabs = []

    def process_indentation(line: str):
        """calculate and transforms indentation characters to tabulars"""
        ident_length = len(ident_char)
        nonlocal tabs

        if line.startswith(ident_char):
            start_point = line.find("<")
            starting_string = line[:start_point]
            indent_char_count = line[:start_point].count(
                ident_char,
            )
            if len(starting_string) != indent_char_count * ident_length:
                last_found = starting_string.rfind(ident_char)
                line = (
                    "\t" * indent_char_count
                    + starting_string[last_found + ident_length :]
                    + line[start_point:]
                )
            else:
                line = "\t" * indent_char_count + line[start_point:]

        indent_char_count = 0
        if line:
            while line[indent_char_count] == "\t":
                indent_char_count = indent_char_count + 1

        tabs.append(indent_char_count)
        return line

    mapping = []

    for line in preparse_html_string():
        line_mapping = []

        line = process_indentation(line)
        line = _correct_non_span(line, default_color)

        words = line.split("<span")
        for word_block in words:
            color = default_color

            color_index = word_block.find("color:")
            if color_index != -1:
                starti = word_block[color_index:].find("#")
                color = word_block[color_index + starti : color_index + starti + 7]

            start_point = word_block.find(">")
            end_point = word_block.find("</span")
            text = word_block[start_point + 1 : end_point]

            text = html.unescape(text)

            if text != "":
                line_mapping.append([text, color])

        mapping.append(line_mapping)

    return mapping, tabs


def _correct_non_span(line_str: str, default_color):
    """fixes and colors  text marks that pygments generate outside of <span></span>-tags and mark those with default color

    Parameters
    ---------
    line_str
        Takes a html element's string to put color to it according to background_color of displayed code.

    Returns
    -------
    :class:`str`
        The generated html element's string with having color attributes.
    """
    words = line_str.split("</span>")
    word_count = len(words)
    line_str = ""

    for i, word in enumerate(words):
        j = word.find("<span") if i != word_count - 1 else len(word)

        temp = ""
        starti = -1
        for k in range(0, j):
            if word[k] == "\t" and starti == -1:
                continue
            else:
                if starti == -1:
                    starti = k
                temp = temp + word[k]
        if temp != "":
            if i != words.__len__() - 1:
                temp = (
                    '<span style="color:'
                    + default_color
                    + '">'
                    + words[i][starti:j]
                    + "</span>"
                )
            else:
                temp = '<span style="color:' + default_color + '">' + words[i][starti:j]
            temp = temp + words[i][j:]
            words[i] = temp
        if words[i] != "":
            line_str = line_str + words[i] + "</span>"

    return line_str


def _generate_html_code_block(
    code: str,
    style: str,
    lexer,
):
    HTML_DIV_STYLE = (
        "border:solid gray;border-width:.1em .1em .1em .8em;padding:.2em .6em;"
    )
    defstyles = "overflow:auto;width:auto;"
    formatter = HtmlFormatter(
        style=style,
        linenos=False,
        noclasses=True,
        cssclass="",
        cssstyles=defstyles + HTML_DIV_STYLE,
        prestyles="margin: 0",
    )
    html: str = highlight(code, lexer, formatter)
    html = (
        f"<!-- HTML generated by {Code.__name__} class by Manim -->\n<!DOCTYPE html>\n"
        + html
    )

    # handle pygments bug of making empty <span></span> tags
    # https://github.com/pygments/pygments/issues/961
    html = html.replace("<span></span>", "")
    return html


def _find_colors(html_string: str):
    """finds background color from html code
    and set default color to opposite of that color"""

    start = html_string.find("background:")
    end = html_string.find(";", start)
    bg_color = html_string[start + 11 : end].strip()
    default_color = opposite_color(bg_color)

    return bg_color, default_color


def opposite_color(color: str):
    if color == "#000000":
        return "#ffffff"
    elif color == "#ffffff":
        return "#000000"
    else:
        # generate opposite color of background color
        new_hexes = []
        for i in range(1, 6, 2):
            hex_str = color[i : i + 2]
            hex_int = int(hex_str, 16)
            new_hex = hex(abs(hex_int - 255)).strip("0x")
            new_hex = new_hex if len(new_hex) > 1 else "0" + new_hex
            new_hexes.append(new_hex)
        return "#" + "".join(new_hexes)


def _insert_line_numbers_in_html(
    html: str, starting_line: int, text_mapping, default_color: str
):
    """Function inserts line numbers to html for proper html output

    Parameters
    ---------
    html
        html string of highlighted code.
    starting_line
        Defines the first line's number in the line count.

    Returns
    -------
    :class:`str`
        The generated html string with having line numbers.
    """
    match = re.search("(<pre[^>]*>)(.*)(</pre>)", html, re.DOTALL)
    if not match:
        return html
    pre_open = match.group(1)
    lines = match.group(2)
    pre_close = match.group(3)

    html = html.replace(pre_close, "</pre></td></tr></table>")
    lines = "\n" + "\n".join(
        str(i) for i in range(starting_line, len(text_mapping) + starting_line)
    )
    pre_tag_opening = pre_open.rstrip('">') + f'color:{default_color};">'
    html = html.replace(
        pre_open,
        "<table><tr><td>" + pre_tag_opening + lines + "</pre></td><td>" + pre_open,
    )
    return html


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
