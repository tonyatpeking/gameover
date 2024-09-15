import traceback
try:
    import colored_traceback.auto
    from colored_traceback.colored_traceback import Colorizer, add_hook, highlight
    colorizer = Colorizer('default', None, False)

except ImportError:
    print('colored_traceback not found, printing traceback in black / white')
    colorizer = None


def colorize_exception(exc):
    if not colorizer:
        return traceback.format_exc()
    exc_type, exc_value, exc_traceback = type(exc), exc, exc.__traceback__
    tb_text = "".join(traceback.format_exception(
        exc_type, exc_value, exc_traceback))
    tb_colored = highlight(tb_text, colorizer.lexer, colorizer.formatter)
    return tb_colored


def print_colorized_exception(exc):
    tb_colored = colorize_exception(exc)
    print(tb_colored)


def lerp_color(start_color: str, stop_color: str, t: float) -> str:
    # Remove the '#' from the beginning of the color strings
    start_color = start_color.lstrip('#')
    stop_color = stop_color.lstrip('#')

    # Convert hex colors to RGB integers
    start_r = int(start_color[0:2], 16)
    start_g = int(start_color[2:4], 16)
    start_b = int(start_color[4:6], 16)

    stop_r = int(stop_color[0:2], 16)
    stop_g = int(stop_color[2:4], 16)
    stop_b = int(stop_color[4:6], 16)

    # Perform linear interpolation
    r = int(start_r + (stop_r - start_r) * t)
    g = int(start_g + (stop_g - start_g) * t)
    b = int(start_b + (stop_b - start_b) * t)

    # Convert back to hex and format as a color string
    return f'#{r:02X}{g:02X}{b:02X}'
