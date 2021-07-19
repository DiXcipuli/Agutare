import MenuHandler as mh

root_node = mh.BasicMenuItem("Root", 0, 1, "Root")

print(isinstance(root_node, mh.RecordSessionItem))