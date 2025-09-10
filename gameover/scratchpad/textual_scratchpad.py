from textual.app import App, ComposeResult
from textual.widgets import Static
from textual.containers import Grid
from gameover.keyboards.ergodox_tony import large

class GridLayoutExample(App):
    CSS_PATH = "styles.tcss"

    def compose(self) -> ComposeResult:
        key_type_and_content = parse_keyboard_layout(large)
        with Grid(id='keyboard-grid'):
            for key_type, key_content in key_type_and_content:
                if key_type == 'long-bottom':
                    continue

                yield Static(key_content, classes=f'key {key_type}')
            





def parse_keyboard_layout(layout_string) -> list[tuple[str, str]]:

    content_rows_only = []
    for line_num, line in enumerate(layout_string.split('\n')):
        if line.strip() == '':
            continue
        if line_num % 2 == 1:
            continue
        content_rows_only.append(line)


    def get_key_content(row, col, content_rows_only, do_not_recurse=False) -> tuple[str, str]:
        key_type = 'placeholder'
        key_content = ''

        line = content_rows_only[row]
        range_start = 1 + col * 6
        range_end = range_start + 5
        key_content = line[range_start:range_end]
        key_content = key_content.strip()

        if key_content != '':
            key_type = 'normal'

        if key_content == '^':
            key_type = 'long'
            # look below to get the content of the long key
            _, key_content = get_key_content(row+1, col, content_rows_only, do_not_recurse=True)

        # look above to check if the key is bottom of a long key
        if row > 0 and key_type == 'normal' and not do_not_recurse:
            above_key_type, _ = get_key_content(row-1, col, content_rows_only)
            if above_key_type == 'long':
                key_type = 'long-bottom'
        
        return key_type, key_content

    key_type_and_content = []

    for row in range(len(content_rows_only)):
        for col in range(15):
            key_type, key_content = get_key_content(row, col, content_rows_only)
            key_type_and_content.append((key_type, key_content))

    return key_type_and_content

if __name__ == "__main__":
    app = GridLayoutExample()
    app.run()
    #print(large)
    #key_type_and_content = parse_keyboard_layout(large)
    #print(key_type_and_content)