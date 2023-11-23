def bake(active_scene,
        background_color = (0,0,0,1),
        image_name:str = 'ImageRender',
        image_prefix:str = 'T_' ,
        image_suffix:str = '' ,
        image_format:str = 'TARGA',
        image_depth:int = 'None',
        display_device:str ='',
        render_denoise = None,
        render_max_samples= None,
        render_engine= 'CYCLES',
        render_using = None,
        render_resolution = (1024,1024),
        sample_clamp_indirect = None,
        filepath = '//BakeOutput/',
        transparent_bdrop = None):  #True,False
 
    
    """
    background_color = 
    image_name =
    image_prefix = 
    image_suffix:str = 
    image_format: 'TARGA', 'OPEN_EXR', 'PNG'
    image_depth: '8','16','32'
    display_device:
    render_denoise:
    render_max_samples:
    render_engine: 'CYCLES','EEVEE'
    render_using: GPU,CPU
    render_resolution: (1024,1024),
    sample_clamp_indirect = None,
    filepath:
    transparent_bdrop:
    """

    if background_color != None:
        background_color_store_R, background_color_store_G, background_color_store_B, background_color_store_A = active_scene.world.node_tree.nodes["Background"].inputs[0].default_value
        active_scene.world.node_tree.nodes["Background"].inputs[0].default_value = background_color

    if image_format != None:
        store_file_format = active_scene.render.image_settings.file_format
        active_scene.render.image_settings.file_format = image_format
    
    if image_depth != None:
        store_image_depth = active_scene.render.image_settings.color_depth

        try:
            active_scene.render.image_settings.color_depth = image_depth
        except TypeError as er:
            self.report({'INFO'}, 'File format does not support assigned bit depth. Leaving previous.')


    if sample_clamp_indirect != None:
        store_sample_clamp_indirect = active_scene.cycles.sample_clamp_indirect
        active_scene.cycles.sample_clamp_indirect = sample_clamp_indirect

    if render_max_samples != None:
        render_max_samples_store = active_scene.cycles.samples
        active_scene.cycles.samples = render_max_samples
    
    if render_denoise != None:
        render_denoise_store = active_scene.cycles.use_denoising
        active_scene.cycles.use_denoising = render_denoise


    if display_device != None:
        store_color_management = active_scene.render.image_settings.color_management
        active_scene.render.image_settings.color_management = 'OVERRIDE'

        store_display_device = active_scene.render.image_settings.display_settings.display_device
        active_scene.render.image_settings.display_settings.display_device = display_device

        store_view_transform = active_scene.view_settings.view_transform
        active_scene.view_settings.view_transform = 'Standard'

        store_look = active_scene.view_settings.look
        active_scene.view_settings.look = 'None'


    if render_resolution != None:
        #Store render resolution
        store_render_resolution = (active_scene.render.resolution_x,active_scene.render.resolution_y)
        active_scene.render.resolution_x, active_scene.render.resolution_y = render_resolution

    if filepath != None:
        backup_filepath = active_scene.render.filepath 
        active_scene.render.filepath = filepath + image_prefix + image_name + image_suffix +'.'+ image_format
        

    if render_engine != None: #Store render engine   
        store_render_engine = active_scene.render.engine #'CYCLES', 'BLENDER_EEVEE'
        active_scene.render.engine = render_engine
    
    if render_using != None:
        render_using_backup = active_scene.cycles.device
        active_scene.cycles.device = render_using

    if transparent_bdrop != None:
        store_transparent_bdrop = active_scene.render.film_transparent                
        active_scene.render.film_transparent = transparent_bdrop




    bpy.ops.render.render(write_still=True)



    #--- RESTORE SETTINGS ---
    if image_format != None:
        active_scene.render.image_settings.file_format = store_file_format

    if render_denoise != None:
        active_scene.cycles.use_denoising = render_denoise_store

    if render_max_samples != None:
        active_scene.cycles.samples = render_max_samples_store

    if sample_clamp_indirect != None:
        active_scene.cycles.sample_clamp_indirect = store_sample_clamp_indirect
    
    if background_color != None:
        active_scene.world.node_tree.nodes["Background"].inputs[0].default_value = (background_color_store_R, background_color_store_G, background_color_store_B, background_color_store_A)

    if display_device != None:
        active_scene.render.image_settings.display_settings.display_device = store_display_device
        active_scene.view_settings.look = store_look
        active_scene.view_settings.view_transform = store_view_transform
        active_scene.render.image_settings.color_management = store_color_management

    if filepath != None:
        active_scene.render.filepath = backup_filepath 
        
    if render_resolution != None:
        active_scene.render.resolution_x = store_render_resolution[0]
        active_scene.render.resolution_y = store_render_resolution[1]

    if render_engine != None:   
        active_scene.render.engine = store_render_engine 

    if render_using != None:
        active_scene.cycles.device = render_using_backup

    if transparent_bdrop != None:
        active_scene.render.film_transparent = store_transparent_bdrop



# Get the node group
def get_material_group_outputs(material_group_name):
    node_group = bpy.data.node_groups.get(material_group_name)
    if node_group:
        # Find all group outputs in the node group
        return [node for node in node_group.nodes if node.type == 'OUTPUT_MATERIAL']


if __name__ == "__main__":
    # Code to run when the script is executed directly
    pass