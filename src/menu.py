from anytree import NodeMixin, RenderTree

class BasicMenuItem(NodeMixin):
    def __init__(self, name, index, size, text_1 = None, text_2 = None, parent = None, children = None):
        self.name = name
        self.index = index
        self.size = size
        self.parent = parent
        self.text_to_display = [text_1, text_2] #To display on the LCD screen, on Line 1 and Line 2
        if children:
            self.children = children

    def execute(self):
        if self.children:
            return self.children[0]

    def back_in_menu(self):
        if self.parent:
            return self.parent

    def next(self):
        if self.index + 1 >= self.size:
            return parent.children[0]
        else:
            return parent.children[self.index + 1]

    def previous(self):
        if self.index - 1 < 0:
            return parent.children[len(self.size) - 1]
        else:
            return parent.children[self.index - 1]

    def get_text(self):
        return self.text_to_display



class MenuHandler:
    def __init__(self, lcd_display):
        self.lcd_display = lcd_display

        # Root level
        root_node = BasicMenuItem("Root", 0, 1)
        # Level 1
        level_1_size = 4
        play_tab_node = BasicMenuItem("play_tab_node", 0, level_1_size, "Play Tab", None, root_node, None)
        practice_node = BasicMenuItem("practice_node", 1, level_1_size, "Practice", None, root_node, None)
        string_test_node = BasicMenuItem("string_test_node", 2, level_1_size, "String test", None, root_node, None)
        motor_pos_node = BasicMenuItem("motor_pos_node", 3, level_1_size, "Servo position", None, root_node, None)
        #Level 2
        