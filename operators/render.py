import bpy,timeit

class OBJECT_OT_lr_cam_bake(bpy.types.Operator):
    bl_idname = "object.lr_cam_bake"
    bl_label = "For baking atlas textures using camera"
    # bl_options = {'REGISTER', 'UNDO'}
    
    render_scene_ao: bpy.props.BoolProperty(name="AO", default=False)
    render_height: bpy.props.BoolProperty(name="Height", default=False)
    render_normal: bpy.props.BoolProperty(name="Normal", default=False, description='Normal Texture input only')
    render_normal_combined: bpy.props.BoolProperty(name="Normal Combined", default=True, description='Normal Texture input + Geometry normals.')
    render_alpha: bpy.props.BoolProperty(name="Alpha", default=True, description='Render Transparency')

    def draw(self, context):
        layout = self.layout.box()
        
        col = layout.row()
        col.prop(self, "render_scene_ao")
        col.prop(self, "render_height")
        col = layout.row()
        col.prop(self, "render_normal")
        col.prop(self, "render_normal_combined")
        col = layout.row()
        col.prop(self, "render_alpha")
        

    

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    
    def execute(self, context): 
        start_time = timeit.default_timer()


        # Name of the node group
        active_scene = bpy.context.scene
        lr_cam_bake_settings = active_scene.lr_cam_bake
        node_group_name = "MF_LR_Bake_Input"
        image_name = lr_cam_bake_settings.img_name
        image_format = 'TGA'
        image_format_height = ''

        bcg_color= active_scene.world.node_tree.nodes["Background"].inputs[0].default_value


        if bpy.data.is_saved == False:
            message = 'File needs to be saved. Exitting.'
            self.report({'ERROR'}, message)
            return {'CANCELLED'}           

        # Get the node group
        def get_material_group_outputs(material_group_name):
            node_group = bpy.data.node_groups.get(material_group_name)
            if node_group:
                # Find all group outputs in the node group
                return [node for node in node_group.nodes if node.type == 'OUTPUT_MATERIAL']


        #Store

        original_filepath = bpy.context.scene.render.filepath

        store_color_management = active_scene.render.image_settings.color_management
        store_display_device = active_scene.render.image_settings.display_settings.display_device
        
        #Store render settings
        store_render_engine = active_scene.render.engine #'CYCLES', 'BLENDER_EEVEE'
        store_samples = active_scene.cycles.samples

        #Store render resolution
        resolution_x = active_scene.render.resolution_x
        resolution_y = active_scene.render.resolution_y

        store_format = active_scene.render.image_settings.file_format
        store_device = active_scene.cycles.device
        store_film_transparency = active_scene.render.film_transparent

        
        mf_check = False
        for mf in bpy.data.node_groups:
            if mf.name == 'MF_LR_Bake_Input':
                mf_check = True
                mf_outputs = get_material_group_outputs(node_group_name)
                
        if mf_check == False:
            message = f'Scene needs to have {node_group_name}. Should be in library. Open material editor and search for it.'
            self.report({'ERROR'}, message)
            return {'CANCELLED'}               


        

        def bake(active_scene,
                 background_color = (0,0,0,1),
                 image_suffix = '' ,
                 image_name = 'ImageRender',
                 image_format = 'TGA',
                 display_device ='sRGB',
                 view = 'Standard',
                 render_denoise = None,
                 render_max_samples= None,
                 render_engine= 'CYCLES',
                 resolution_x = 1024,
                 resolution_y = 1024,
                 sample_clamp_indirect = None):

            if sample_clamp_indirect != None:
                store_sample_clamp_indirect = active_scene.cycles.sample_clamp_indirect
                active_scene.cycles.sample_clamp_indirect = sample_clamp_indirect

            if render_max_samples != None:
                render_max_samples_store = active_scene.cycles.samples
                active_scene.cycles.samples = render_max_samples
            
            if render_denoise != None:
                render_denoise_store = active_scene.cycles.use_denoising
                active_scene.cycles.use_denoising = render_denoise

            if background_color != None:
                background_color_store_R, background_color_store_G, background_color_store_B, background_color_store_A = active_scene.world.node_tree.nodes["Background"].inputs[0].default_value
                active_scene.world.node_tree.nodes["Background"].inputs[0].default_value = background_color

            active_scene.render.engine = render_engine
            
            active_scene.render.image_settings.display_settings.display_device = display_device
            active_scene.render.image_settings.view_settings.view_transform = view
    
            bpy.context.scene.render.filepath = '//RenderOutput/' + 'T_' + image_name + image_suffix +'.'+ image_format
            
            active_scene.render.resolution_x = resolution_x
            active_scene.render.resolution_y = resolution_y
            a,b,c,d = active_scene.world.node_tree.nodes["Background"].inputs[0].default_value
            print(f'Background Color R:{a} G:{b} B:{c} A:{d}')
            print(f'Denoise: {render_denoise}')
            print(f'Max Samples: {render_max_samples}')
            bpy.ops.render.render(write_still=True)

            #Restore render settings
            if render_denoise != None:
                active_scene.cycles.use_denoising = render_denoise_store

            if render_max_samples != None:
                active_scene.cycles.samples = render_max_samples_store

            if sample_clamp_indirect != None:
                active_scene.cycles.sample_clamp_indirect = store_sample_clamp_indirect
            
            if background_color != None:
                active_scene.world.node_tree.nodes["Background"].inputs[0].default_value = (background_color_store_R, background_color_store_G, background_color_store_B, background_color_store_A)




        active_scene.render.image_settings.file_format = 'TARGA'
        active_scene.render.image_settings.color_management = 'OVERRIDE'
        active_scene.render.film_transparent = True

        if lr_cam_bake_settings.render_device == 'OP1':
            active_scene.cycles.device = 'CPU'
        elif lr_cam_bake_settings.render_device == 'OP2':
            active_scene.cycles.device = 'GPU'
        

        
        # -------------- LOOPING OVER MG OUTPUTS AND RENDERING EACH --------------
        current_render = 0
        
        for output in mf_outputs:
            output.is_active_output = True

            if output.name == 'Albedo':
                bake(active_scene= active_scene,
                     image_suffix= '_A',
                     background_color=(0,0,0,1),
                     image_name= image_name,
                     image_format= image_format,
                    #  display_device = 'sRGB',
                     view = 'Standard',
                     resolution_x=lr_cam_bake_settings.resolution_x,
                     resolution_y=lr_cam_bake_settings.resolution_y,
                     
                     render_denoise=False,
                     render_max_samples= 1)
            
            if self.render_alpha:
                if output.name == 'Alpha':
                    bake(active_scene= active_scene,
                        image_suffix= '_K',
                        background_color=(0,0,0,1),
                        image_name= image_name,
                        image_format= image_format,
                        #  display_device = 'None', #Not needed with blender 4.0, Does not affect output image... ?
                        view = 'Raw',
                        resolution_x=lr_cam_bake_settings.resolution_x,
                        resolution_y=lr_cam_bake_settings.resolution_y,
                        
                        render_denoise=False,
                        render_max_samples= 1)   
            

            if self.render_normal:
                if output.name == 'Normal':
                    bake(active_scene= active_scene,
                        image_suffix= '_N',
                        background_color=(0.5,0.5,1,1),
                        image_name= image_name,
                        image_format= image_format,
                        #  display_device = 'None',
                        view = 'Raw',
                        resolution_x=lr_cam_bake_settings.resolution_x,
                        resolution_y=lr_cam_bake_settings.resolution_y,
                        
                        render_denoise=False,
                        render_max_samples= 1)
            
            
            if self.render_normal_combined:
                if output.name == 'Normal_Combined':
                    bake(active_scene= active_scene,
                        image_suffix= 'Combined_N',
                        background_color=(0.5,0.5,1,1),
                        image_name= image_name,
                        image_format= image_format,
                        #  display_device = 'None',
                        view = 'Raw',
                        resolution_x=lr_cam_bake_settings.resolution_x,
                        resolution_y=lr_cam_bake_settings.resolution_y,
                        
                        render_denoise=False,
                        render_max_samples= 1)



            if output.name == 'Occlusion_Texture':
                bake(active_scene= active_scene,
                     image_suffix= '_O',
                     background_color=(1,1,1,1),
                     image_name= image_name,
                     image_format= image_format,
                    #  display_device = 'None', 
                     view = 'Raw',
                     resolution_x=lr_cam_bake_settings.resolution_x,
                     resolution_y=lr_cam_bake_settings.resolution_y,
                     
                     render_denoise=False,
                     render_max_samples= 1)   
            
            if self.render_scene_ao: 
                if output.name == 'Occlusion_Scene':
                    bake(active_scene= active_scene,
                        image_suffix= '_Scene_O',
                        background_color=(1,1,1,1), 
                        image_name = image_name, 
                        image_format = image_format, 
                        #  display_device = 'None',
                        resolution_x = lr_cam_bake_settings.resolution_x,
                        resolution_y = lr_cam_bake_settings.resolution_y,

                        render_denoise=lr_cam_bake_settings.render_ao_denoise,
                        render_max_samples= lr_cam_bake_settings.render_ao_denoise_samples,
                        sample_clamp_indirect = 0.0001)   
         
            if output.name == 'Roughness':
                bake(active_scene= active_scene,
                     image_suffix= '_R',
                     background_color=(0,0,0,1),
                     image_name= image_name,
                     image_format= image_format,
                    #  display_device = 'None',
                     view = 'Raw',
                     resolution_x=lr_cam_bake_settings.resolution_x,
                     resolution_y=lr_cam_bake_settings.resolution_y,

                     render_denoise=False,
                     render_max_samples=1)   
            
            if output.name == 'Metallic':
                bake(active_scene= active_scene,
                     image_suffix= '_M',
                     background_color=(0,0,0,1),
                     image_name= image_name,
                     image_format= image_format,
                    #  display_device = 'None',
                     view = 'Raw',
                     resolution_x=lr_cam_bake_settings.resolution_x,
                     resolution_y=lr_cam_bake_settings.resolution_y,
                     
                     render_denoise=False,
                     render_max_samples=1)
            
            if self.render_height:
                if output.name == 'Height':
                    bake(active_scene= active_scene,
                        image_suffix= '_H',
                        background_color=(0.5,0.5,0.5,1),
                        image_name= image_name,
                        image_format= image_format_height,
                        #  display_device = 'None',
                        view = 'Raw',
                        resolution_x=lr_cam_bake_settings.resolution_x,
                        resolution_y=lr_cam_bake_settings.resolution_y,
                        
                        render_denoise=False,
                        render_max_samples= 1)   
            
            # message = f'{(current_render+1)} of {len(mf_outputs)} done.'
            elapsed_time = timeit.default_timer() - start_time
            message = f'Done in {elapsed_time:.2f}s.'
            self.report({"INFO"}, message=message)
  




        #Restore to original filepath
        bpy.context.scene.render.filepath = original_filepath
 
        #Restore display_device settings
        active_scene.render.image_settings.color_management= store_color_management
        active_scene.render.image_settings.display_settings.display_device = store_display_device

        #Restore render settings
        active_scene.render.engine = store_render_engine

        #Restore render resolution
        active_scene.render.resolution_x = resolution_x
        active_scene.render.resolution_y = resolution_y

        active_scene.render.image_settings.file_format = store_format
        active_scene.render.film_transparent = store_film_transparency

        active_scene.cycles.device = store_device
        return {'FINISHED'}





