from textual.app import App, ComposeResult
from textual.widgets import Static
from gameover.keyboards.ergodox_tony import large

class GridLayoutExample(App):
    CSS_PATH = "styles.tcss"

    def compose(self) -> ComposeResult:

        for i in range(149):
            yield Static(f"{i+1}", classes="box")





def parse_keyboard_layout(layout_string):

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
            key_type = 'content'

        if key_content == '^':
            key_type = 'long_top'
            # look below to get the content of the long key
            _, key_content = get_key_content(row+1, col, content_rows_only, do_not_recurse=True)

        # look above to check if the key is bottom of a long key
        if row > 0 and key_type == 'content' and not do_not_recurse:
            above_key_type, _ = get_key_content(row-1, col, content_rows_only)
            if above_key_type == 'long_top':
                key_type = 'long_bottom'
        
        return key_type, key_content

    for row in range(len(content_rows_only)):
        for col in range(15):
            key_type, key_content = get_key_content(row, col, content_rows_only)
            print(row, col, key_type, key_content)

if __name__ == "__main__":
    # app = GridLayoutExample()
    # app.run()
    #print(large)
    parse_keyboard_layout(large)