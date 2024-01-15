import bpy,os
         

def get_path_to_addon(addon_folder_name):
    script_folder = bpy.utils.script_paths()
    script_folder.reverse()

    for path in script_folder:
        print(path)
        path = os.path.join(path,'addons')
        if os.path.exists(path):
            if addon_folder_name in os.listdir(path):
                return os.path.join(path,addon_folder_name)
            else:
                return None

# Get the node group
def get_material_group_outputs(material_group_name):
    node_group = bpy.data.node_groups.get(material_group_name)
    if node_group:
        # Find all group outputs in the node group
        return [node for node in node_group.nodes if node.type == 'OUTPUT_MATERIAL']


if __name__ == "__main__":
    # Code to run when the script is executed directly
    pass