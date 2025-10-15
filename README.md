# gameover

## Insight

- Context switching is a pain
- Unified custom context
- E.g. VLC note taker
    - Normally this has to be done in the following steps
        - Context switch to VLC
        - Seek video
        - Mental note on time stamp
        - Context switch to note taker
        - Manually type in time stamp and make note
    - With custom context
        - Special context include VLC and note taker
        - Gameover intercepts all inputs to prevent hotkey clashes
        - Any hotkeys are sent to either VLC or Note Taker or both depending on config
        - Hotkey remapping
        - Now no more context switching

## Playing with markdown and HTML

<pre>
<button>foo</button> <button>foo</button>
<button>foo</button> <button>foo</button>
</pre> 

## Details

<details>

<summary>summary goes here</summary>

### You can add a header

You can add text within a collapsed section.

You can add an image or a code block, too.

```ruby
   puts "Hello World"
```

<details>
<summary>Can I nest details?</summary>

### Lets see

</details>

</details>

## Gameover

gameover (Gamer Overlay) is a Python project that provides an overlay for desktop environments inspired by game keyboard shortcuts and overlays.

## Installation

## Features

- GUI for visual feedback and configuration.
- Context awareness.
- Remap on the fly.
- Central location for all keyboard mappings.
- Switch between multiple keyboard layouts and configurations.

## Usage

## Logging and Debugging

- Log all events, this can help with debugging when you want to know how the program got into a certain state.

## GUI

If you are here you are probably a power user and hate GUIs. Hear me out. The animosity towards GUIs is mostly because of mouse usage. This GUI is designed to be used by a keyboard. The main advantage of this GUI is so that you have visual feedback of what layer you are on, what key does what, and easy configuration on the fly.

#### Layout

- [Installation](#installation)
- Tabs with layers like oryx https://configure.zsa.io/ergodox-ez/layouts/Yn9EZ/B556v/0
- Layer activation criteria
    - Window context
    - Layer Toggle / Hold Key



### Getting started with the GUI

#### Input Mapping

- It is recommended that you first disable all hardware keyboard layers and shortcuts / modifiers etc. (Or just don't use those keys) Gameover is designed to be used with a clean slate. You should be able to achieve all hardware remapping functionality extra benefits.
- Pick a keyboard layout that matches your hardware or is close enough.
- (Optional) Modify the layout by adding or removing keys.
- Start the keyboard mapper. This will prompt you to press each key on your keyboard. Only one key should be pressed at a time. This will create a map of your keyboard. If you make a mistake you can restart or press the previous key button with your mouse.
- Do the same for the mouse mapper.
- Now gameover has a internal map of your keyboard and mouse.
- You can repeat the process for different keyboards or mouse devices.

#### Window Context Mapping

- Window class / title 

#### Events

- Window Context Change
- Hardware Key Press
- Custom (time of day, repeating, triggered by watcher, etc.)
- Watcher can watch website, api, screen section, etc.
- Set watcher frequency
- Brain Computer Interface

#### Dynamic Mapping

- Different mapping based on State / Layer / Context


#### Action

- Send Software Key Press 
- Move mouse
- Window move
- Execute bash / python / cmd script
- Send notification
- Play macro


```

class 

event
    key.press
context
    when
action
    call fn
    set state

```

#### Image Tagger Dedupe Organizer

- Embedding
    - Model
    - Bits
- Tagging
- Dedupe




#### Action Buffers

- YAML
- Undo Redo Tree

Example
```yaml
- function_1: arg1
- function_2: [arg1, arg2]
- function_3: {arg1_name: arg1_value, arg2_name: arg2_value}
- function_4:
    - arg1_name: arg1_value
    - arg2_name: arg2_value
```

Schema
```yaml



```
- Clipboard List
    - Clipboard Watcher Always Pushes to Clipboard List
    - PushTop PushBottom PopTop PopBottom
- Paste / Execute Buffer Item




#### Support different backends



#### Support screen capture, mouse move, window move, based on backend

#### Output Mapping

- Start the GUI.
- Select the Output Mapping tab.


## Contributing

If you would like to contribute to gameover, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them.
4. Push your changes to your forked repository.
5. Submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.
```
This file is intentionally left blank.
```