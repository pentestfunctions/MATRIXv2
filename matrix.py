import sys
from datetime import datetime
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import subprocess

# Initialize Pygame
pygame.init()
screen_info = pygame.display.Info()
screen = pygame.display.set_mode((screen_info.current_w, screen_info.current_h), pygame.NOFRAME)
pygame.display.set_caption("M.A.T.R.I.X - Multi-purpose Automated Testing and Reconnaissance Interface for eXploits")

# Colors and Fonts
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)
HIGHLIGHT = (128, 128, 128)
font = pygame.font.SysFont("monospace", 20)
small_font = pygame.font.SysFont("monospace", 15)

# Global Variables
menus = {}
selected_option = None
current_menu = 'Main'
command_state = ''
mouse_pos = (0, 0)
menu_stack = [] 
input_mode = False
input_text = ""
input_active = False
base_command = ''
additional_inputs = ''
command_options = {}
current_selection = 0  # Index of the currently selected menu option

# Output Area Dimensions and Position (Subprocess/command output text area)
output_area_width = 400
output_area_height = screen_info.current_h - 100
output_area_x = screen_info.current_w - output_area_width - 800 # From the right side
output_area_y = 250 # From the top
scroll_y = 0  # Tracks the vertical scroll position so we can scroll the output
subprocess_output = ""  # Global variable to hold subprocess output

def load_commands():
    global menus, command_args
    menus = {
        "Main": ["Passive Reconnaissance", "Active Reconnaissance"],
        "Passive Reconnaissance": ["whois", "whatweb", "ping"],
        "Active Reconnaissance": ["dirsearch"],
        "whois": ["Run Command", "Enter Target"],
        "whatweb": ["Run Command", "verbose", "aggressive_scan", "suppress_errors", "Enter Target"],
        "ping": ["Run Command", "Enter Target"],
        "dirsearch": ["Run Command", "target", "crawl"]
    }
    command_args = {
        "whois": "whois",
        "whatweb": "whatweb",
        "ping": "ping",
        "verbose": "--verbose",
        "aggressive_scan": "--aggressive",
        "suppress_errors": "--no-errors",
        "target": "--target",
        "crawl": "--crawl"
    }

def load_parent_mapping():
    global menus, menu_parent_map
    menu_parent_map = {}
    for parent, children in menus.items():
        for child in children:
            menu_parent_map[child] = parent  # Map each child to its parent

load_commands()
load_parent_mapping()

def get_current_options():
    if current_menu == "Main":
        return menus[current_menu] + ["Exit"]  # Add "Exit" option on the main menu
    else:
        return menus[current_menu] + (["Back"] if current_menu != "Main" else [])

def draw():
    screen.fill(BLACK)
    screen_width, screen_height = screen_info.current_w, screen_info.current_h

    options_start_y = 250  # Start drawing menu options a bit lower
    options = get_current_options()
    for index, option in enumerate(options):
        if index == current_selection:
            highlight_color = GRAY
        else:
            highlight_color = BLACK

        highlight = pygame.Rect(100, options_start_y + index * 40, 400, 25)
        pygame.draw.rect(screen, highlight_color, highlight)
        draw_text(option, 105, options_start_y + index * 40, GREEN)

    title_text = "M.A.T.R.I.X - Multi-purpose Automated Testing and Reconnaissance Interface for eXploits"
    title_width, title_height = font.size(title_text)
    title_x = screen_width // 2 - title_width // 2
    title_y = 20
    draw_text(title_text, title_x, title_y, GREEN)

    multiline_text = "==============================\nWake up Robot.\nThe Matrix has you...\nFollow the white rabbit...\nKnock knock, Robot.\n==============================\n"
    draw_multiline_text(multiline_text, screen_width // 2, title_y + title_height + 10, GRAY)

    # Display date and time at the top right
    now = datetime.now()
    date_time_string = now.strftime("%Y-%m-%d %H:%M:%S")
    draw_text(date_time_string, screen_width - 300, 20, GREEN)

    # Display the current command state at the bottom
    draw_text("Command: " + command_state, 100, screen_height - 40, GREEN)

    draw_subprocess_output()
    pygame.display.flip()

def draw_multiline_text(text, center_x, top_y, color):
    lines = text.split('\n')
    total_height = len(lines) * font.get_linesize()
    current_y = top_y

    for line in lines:
        line_width, line_height = font.size(line)
        text_surface = font.render(line, True, color)
        line_x = center_x - line_width // 2
        screen.blit(text_surface, (line_x, current_y))
        current_y += line_height

def draw_text(text, x, y, color):
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))

def update_mouse_position(pos):
    global mouse_pos
    mouse_pos = pos
    update_current_selection_from_mouse(pos)

def handle_click(pos):
    global current_menu, selected_option, menu_stack, running, command_state, command_options
    options = get_current_options()
    y = 250
    selected_option = None
    for index, option in enumerate(options):
        if pygame.Rect(100, y + index * 40, 400, 35).collidepoint(pos):
            selected_option = index
            break
    if selected_option is not None:
        selected_option_text = options[selected_option]
        if selected_option_text == "Exit":
            running = False
            return
        elif selected_option_text == "Back":
            handle_back_navigation()
        else:
            handle_option_selection(selected_option_text)

def handle_option_selection(option):
    global current_menu, base_command, command_options, command_state, input_mode, input_text, subprocess_output

    if option == "Enter Target":
        input_mode = True
        input_text = ""

    elif option == "Run Command":
        print(f"{command_state}")
        try:
            process = subprocess.Popen(command_state, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            output, _ = process.communicate()
            subprocess_output = output
        except subprocess.CalledProcessError as e:
            subprocess_output = f"Error: {e}\n{e.output}"

    elif option in menus:
        current_menu = option
        menu_stack.append(current_menu)

        # command selection within a submenu
        if option in command_args:
            base_command = option
            command_options = {}  # reset when a new command is selected
            rebuild_command()
        else:
            print(f"Navigation to menu: {option}")
    elif option in command_args:
        toggle_command_option(option)
        rebuild_command()
    else:
        print(f"Unhandled option: {option}")

def draw_subprocess_output():
    global scroll_y
    pygame.draw.rect(screen, BLACK, (output_area_x, output_area_y, output_area_width, output_area_height))
    
    lines = subprocess_output.split('\n')
    y_offset = -scroll_y
    for line in lines:
        if y_offset > output_area_height:  # stop drawing if we reach the bottom of the output area
            break
        if y_offset + 20 >= 0:
            text_surface = small_font.render(line, True, GREEN)
            screen.blit(text_surface, (output_area_x + 5, output_area_y + y_offset))
        y_offset += 20

def toggle_command_option(option):
    global command_options
    command_options[option] = not command_options.get(option, False)

def rebuild_command():
    global command_state, base_command, command_options, command_args
    
    # Initialize command_state with the base_command's command-line representation.
    command_state = command_args.get(base_command, "")

    # Append all enabled options to the command.
    for option, enabled in command_options.items():
        if enabled and option in command_args:
            command_state += " " + command_args[option]

    print(f"Command State: {command_state}")

def handle_back_navigation():
    global current_menu, command_state, menu_parent_map
    if menu_stack:
        menu_stack.pop()
        current_menu = menu_stack[-1] if menu_stack else "Main"
        if current_menu == "Main":
            command_state = ''  # Reset command state when going back to the main menu
        else:
            pass

def draw_input_field():
    global input_text, input_active
    # Use screen_info to get screen dimensions
    screen_width, screen_height = screen_info.current_w, screen_info.current_h
    
    input_box = pygame.Rect(100, screen_height - 100, 140, 32)
    color = GREEN if input_active else (100, 100, 100)  # active color vs inactive
    
    # Draw the input box
    pygame.draw.rect(screen, color, input_box)
    text_surface = font.render(input_text, True, GREEN)
    screen.blit(text_surface, (input_box.x + 5, input_box.y + 5))
    
    pygame.display.flip()

def handle_keydown_event(event):
    global current_selection, input_mode, input_text, command_state
    if input_mode:
        if event.key == pygame.K_RETURN:
            # Append the input text to the command_state
            if base_command:  # Check if a base command is set
                command_state += " " + input_text
            else:
                command_state = input_text
            print(f"Command updated: {command_state}")
            input_text = ""  # Reset input text
            input_mode = False  # Exit input mode
        elif event.key == pygame.K_BACKSPACE:
            input_text = input_text[:-1]  # Remove the last character if backspace is pressed
        else:
            if event.unicode.isprintable():
                input_text += event.unicode
    else:
        if event.key == pygame.K_UP:
            current_selection = max(current_selection - 1, 0)
        elif event.key == pygame.K_DOWN:
            options = get_current_options()
            current_selection = min(current_selection + 1, len(options) - 1)
        elif event.key == pygame.K_RETURN:
            select_option(current_selection)

def update_current_selection_from_mouse(pos):
    global current_selection
    options_start_y = 250
    option_height = 40
    for index, option in enumerate(get_current_options()):
        option_rect = pygame.Rect(100, options_start_y + index * option_height, 400, 25)
        if option_rect.collidepoint(pos):
            current_selection = index
            break

def select_option(index):
    global current_menu, running, command_state

    options = get_current_options()
    if index < len(options):
        selected_option_text = options[index]

        if selected_option_text == "Exit":
            running = False
        elif selected_option_text == "Back":
            handle_back_navigation()
        else:
            handle_option_selection(selected_option_text)

def handle_mouse_button_down(event):
    global scroll_y
    if event.button == 4:  # Scroll up
        scroll_y = max(scroll_y - 20, 0)  # Prevent scrolling above the start
    elif event.button == 5:  # Scroll down
        scroll_y += 20  # Scroll down

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEMOTION:
            update_mouse_position(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            handle_mouse_button_down(event)
            handle_click(event.pos)
        elif event.type == pygame.KEYDOWN:
            handle_keydown_event(event)

    draw()
    if input_mode:
        draw_input_field()

pygame.quit()
sys.exit()
