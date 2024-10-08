import bpy,timeit,os

from .. import config


class LR_TOOLS_OT_r2t_new_camera(bpy.types.Operator):
    bl_idname = "lr_tools.r2t_new_camera"
    bl_label = "For baking atlas textures using camera"
    bl_description = "Add camera into scene. \nAdded 2 meters above world zero. Camera needs to have a name 'LR_RenderToTexture'"
    # bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def execute(self, context):
        lr_cam_bake = context.scene.lr_render2texture
        # cursor_location = bpy.context.scene.cursor.location
        
        bpy.ops.object.camera_add(enter_editmode=False, align='WORLD', location=(0, 0, 1), rotation=(0, 0, 0), scale=(1, 1, 1))

        render_camera = bpy.context.active_object
        render_camera.name = 'LR_RenderToTexture'
        render_camera.data.name = 'LR_RenderToTexture_data'
        render_camera.data.type = 'ORTHO'
        render_camera.data.ortho_scale = 2
        render_camera.data.display_size = 0.3

        bpy.context.scene.render.resolution_x = 1024
        bpy.context.scene.render.resolution_y = 1024
        bpy.context.scene.camera = render_camera   
        
        # Get the node group
        return {'FINISHED'}


class LR_TOOLS_OT_r2t_append_ng(bpy.types.Operator):
    bl_idname = "lr_tools.r2t_append_ng"
    bl_label = "Adds material group into materials on selected objects"
    bl_description = "Adds material group into materials on selected objects"
    # bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):
        
        node_group_name = "NG_LR_R2T"
        node_group = bpy.data.node_groups.get(node_group_name)
        selected_objects = bpy.context.selected_objects
        
        used_append = False
        if node_group == None:
            file_path = os.path.join(config.addon_folder_location,'resources','lr_render2texture.blend')
            inner_path = "NodeTree"
            bpy.ops.wm.append(filepath=str(os.path.join(file_path, inner_path, node_group_name)), directory=str(os.path.join(file_path, inner_path)),filename=str(node_group_name))
            node_group = bpy.data.node_groups.get(node_group_name)
            used_append = True

        if node_group:
            for obj in selected_objects: 
                if used_append: #Append above deselects it.
                    obj.select_set(True)

                if obj.type == 'MESH':
                    for material_slot in obj.material_slots:
                        material = material_slot.material

                        has_nodegroup = False
                        
                        # has_nodegroup = any(node.type == 'GROUP' and type(node.node_tree) != type(None) and node.node_tree.name == node_group_name  for node_tree.nodes in material.node_tree.nodes if material.use_nodes)
                        if material.use_nodes:
                            node_tree = material.node_tree
                            
                            for node in node_tree.nodes: # Check if the node group is not already present in the material
                                if node.type == 'GROUP' and type(node.node_tree) != type(None):
                                    if node.node_tree.name == node_group_name:
                                        has_nodegroup = True
                                        break
                                    
                            if has_nodegroup == False:
                                group_node = node_tree.nodes.new(type='ShaderNodeGroup')
                                group_node.node_tree = node_group
                                group_node.name = node_group_name

        else:
            message = "Can't append MG."
            self.report({'WARNING'}, message)
        
        
        # Get the node group
        return {'FINISHED'}

    
def get_materials_list(objs)-> list:
    materials_list = []

    # Iterate through all objects in the scene
    for obj in objs:
        # Check if the object has materials
        if obj.type == 'MESH' and obj.data.materials:
            # Iterate through the materials of the object
            for material_slot in obj.material_slots:
                material = material_slot.material
                if material not in materials_list:
                    materials_list.append(material)

    return materials_list


class LR_TOOLS_OT_R2T_Render(bpy.types.Operator):
    bl_idname = "lr_tools.r2t_render"
    bl_label = "For baking atlas textures using camera"
    bl_description = "Render selected textures. Info about renders in console\nOutput images are with straight alpha. Final image RGB multiplied by its Alpha should give correct output"
    # bl_options = {'REGISTER', 'UNDO'}
    


    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def execute(self, context):
        has_errors = False
        
        # Name of the node group
        active_scene = bpy.context.scene
        lr_cam_bake = context.scene.lr_render2texture



        def rewire_from_bsdf_to_bake_node(bake_node, material) -> None:
            '''Only connected if BSDF has input and Bake Node input is empty'''

            bake_node_material = None
            brdf_node = None
            for node in material.node_tree.nodes:
                if bpy.types.ShaderNodeGroup == type(node):
                    if node.node_tree == bake_node:
                        if bake_node_material == None:
                            bake_node_material = node


                if type(node) == bpy.types.ShaderNodeBsdfPrincipled:
                    if brdf_node == None: #Take first one
                        brdf_node = node

            if bake_node_material == None or brdf_node == None:
                return None


            def connect(bsdf_input_name , bake_input_name):
                if brdf_node.inputs[bsdf_input_name].is_linked == True and bake_node_material.inputs[bake_input_name].is_linked == False:

                    #Normal relink need to take 'Normal Map' node into consideration. Takes Color input.
                    if bsdf_input_name == 'Normal':
                        if brdf_node.inputs[bsdf_input_name].links[0].from_node.type == "NORMAL_MAP":
                            if brdf_node.inputs[bsdf_input_name].links[0].from_node.inputs["Color"].is_linked:
                                material.node_tree.links.new(brdf_node.inputs[bsdf_input_name].links[0].from_node.inputs["Color"].links[0].from_socket, bake_node_material.inputs[bake_input_name])
 
                    else:
                        material.node_tree.links.new(brdf_node.inputs[bsdf_input_name].links[0].from_socket, bake_node_material.inputs[bake_input_name])

            bsdf_and_bake_input_matches = (("Base Color","Albedo"),("Alpha","Alpha"),("Normal","Normal"),("Roughness","Roughness"),("Metallic","Metallic"))

            for match in bsdf_and_bake_input_matches:
                connect(match[0],match[1])



        def get_unique_curves(curves):
        
            """
            Obly works with bezier curves now
            This function takes a list of curves and returns a set of unique curves.
            A curve is considered unique if its first and last points location do not match 
            the first and last points of any other curve in the list.

            Parameters:
            list_of_curves (list): A list of curves to check for uniqueness.

            Returns:
            set: A set of unique curves from the input list.
            """
            
            check_against_curves = curves.copy()

            unique= set()
            for curve in curves:
                        
                found_duplicates = []
                for _ in check_against_curves:
                    if _ == curve:
                        continue
                    
                    if (curve.data.splines[0].bezier_points[0].co == _.data.splines[0].bezier_points[0].co) and (curve.data.splines[0].bezier_points[-1].co == _.data.splines[0].bezier_points[-1].co) and (curve.matrix_world.to_translation() == _.matrix_world.to_translation()):
                        found_duplicates.append(_)
                        
                for dup in found_duplicates:
                    if dup in check_against_curves:
                        check_against_curves.remove(dup)
                
                if curve in check_against_curves:
                    unique.add(curve)
                
                if curve in check_against_curves:
                    check_against_curves.remove(curve)
                
            return unique    

        
        # Get the node group
        def get_material_group_outputs(material_group_name):
            node_group = bpy.data.node_groups.get(material_group_name)

            if node_group:
                # Find all group outputs in the node group
                return [node for node in node_group.nodes if node.type == 'OUTPUT_MATERIAL']
            

        start_time = timeit.default_timer()

        store_obj_selection = bpy.context.selected_objects #Excluding active obj
        store_obj_active = bpy.context.active_object
        

        node_group_name = "NG_LR_R2T"
        image_name = lr_cam_bake.img_name
        image_format = 'TGA'
        image_format_height = ''

        # bcg_color = active_scene.world.node_tree.nodes["Background"].inputs[0].default_value


        if bpy.data.is_saved == False:
            message = 'File needs to be saved first.'
            self.report({'ERROR'}, message)
            return {'CANCELLED'}           

            
        # ng_check = False
        # for mf in bpy.data.node_groups:
        #     if mf.name == node_group_name:
        #         ng_check = True


        
        # if ng_check == False:
        #     message = f'Scene needs to have {node_group_name}. Should be in library. Open material editor and search for it.'
        #     self.report({'ERROR'}, message)
        #     return {'CANCELLED'}      

        # mf_outputs = get_material_group_outputs(node_group_name)
        


        #Filter objects inside collection and get only meshes and instanced collections
        objects_eval = {}
        render_visibility_store = []

        objects_rendered = []        
        bpy.ops.object.select_all(action='DESELECT')
        


        objs_enabled = [obj for obj in bpy.context.view_layer.objects if obj.lr_render2texture.object_mode ==  'RENDERED']
        if len(objs_enabled) == 0:
            message = f"No objects are set to be 'Rendered'."
            self.report({'ERROR'}, message)
            return {'CANCELLED'}    
        
        
        
        rendered_objs_set = set(objs_enabled)

        # all_objs_set = set(bpy.data.objects)
        all_objs_set = set(bpy.context.view_layer.objects)
        objs_disabled = list(all_objs_set.difference(rendered_objs_set)) 


        index = 0   
        for obj in objs_enabled:
            
            print(f"Enabled: {obj.name}")
            if obj.type == 'MESH':
                objects_eval[index] = {'obj': obj, 'render_visibility_init': obj.hide_render, 'type': 'MESH'}
                index += 1
                objects_rendered.append(obj)

            elif obj.type == 'EMPTY' and obj.instance_type == 'COLLECTION':
                obj.select_set(True)
                objects_eval[index] = {'obj': obj, 'render_visibility_init': obj.hide_render, 'type': 'COLLECTION'}
                index += 1

            elif obj.type == "CURVE":
                objects_rendered.append(obj)


        for idx in objects_eval:
            if objects_eval[idx]['type'] == 'COLLECTION':

                # objects_eval[idx]['obj'].select_set(True) #select object to be duplicated
                objects_eval[idx]['obj'].hide_render = True
        
        #Duplicate all selected collections
        bpy.ops.object.duplicate(linked=True) 
        
        collection_names = [] 
        for collection in bpy.context.selected_objects: #Store collection names which becomes empty after flatten. For later deletion. 

            if collection.type== 'EMPTY' and collection.instance_type == 'COLLECTION':
                collection_names.append(collection.name)
        
        
        #Flatten collection instances
        bpy.ops.object.duplicates_make_real(use_base_parent=False, use_hierarchy=False)

        empty_leftover = [] #After flatten the empty obj isn't selected.
        for name in collection_names: 
            obj = bpy.data.objects.get(name)
            if obj is not None and obj.type == 'EMPTY':
                empty_leftover.append(obj)    

        flattened_objects = bpy.context.selected_objects


        # BLENDER FIX Currently bug in Blender where if collection instance has a curve it. After flatten operation they are duplicated 
        flattened_objects_curves = []
        for obj in flattened_objects:
            if obj.type == 'CURVE':
                flattened_objects_curves.append(obj)
        
        flattened_objects_curves_unique_set = list(get_unique_curves(flattened_objects_curves))
        
        # print(f'{flattened_objects_curves_unique_set= }')
        bpy.ops.object.select_all(action='DESELECT')
        for obj in flattened_objects_curves:
            if obj not in flattened_objects_curves_unique_set:
                obj.select_set(True)   
                flattened_objects.remove(obj)   

        bpy.ops.object.delete()               
        # flattened_objects_curves_set = set(flattened_objects_curves)

        # flattened_objects_curves_unique_set_inverted = flattened_objects_curves_set.difference(flattened_objects_curves_unique_set)
        
        # for obj in flattened_objects_curves_unique_set_inverted:
        #     if obj in flattened_objects_curves:
        #         flattened_objects.remove(obj)

        # for obj in flattened_objects_curves_unique_set_inverted:
        #     obj.select_set(True)      

        # bpy.ops.object.delete()


        #END OF FIX. Remove once fixed by Blender. 
        
    
        objects_rendered.extend(flattened_objects)




        def create_mat(name):
            r2t_material = bpy.data.materials.new(name)
            r2t_material.use_nodes = True
            return r2t_material


        # if lr_cam_bake.add_missing_ng == True:
        s_select = bpy.context.selected_objects
        bpy.ops.object.select_all(action='DESELECT')
        r2t_material = bpy.data.materials.get("M_R2T_Created") #Only needed when objecy with material is present

        for obj in objects_rendered:
            if len(obj.material_slots) == 0: #Assign material if missing ID slot  
                if r2t_material == None:
                    r2t_material = create_mat("M_R2T_Created")

                obj.data.materials.append(r2t_material)
            
            if obj.material_slots[0].material == None: #Assign if material ID is missing material
                if r2t_material == None:
                    r2t_material = create_mat("M_R2T_Created")
                obj.material_slots[0].material = r2t_material

            obj.select_set(True)

        bpy.ops.lr_tools.r2t_append_ng()

        bpy.ops.object.select_all(action='DESELECT')
        for obj in s_select:
            obj.select_set(True)

        mf_outputs = get_material_group_outputs(node_group_name)

        node_group_name = "NG_LR_R2T"
        bake_node_group = bpy.data.node_groups.get(node_group_name)

        mats = get_materials_list(objects_rendered)
        for mat in mats:
            has_group = False

            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if type(node) != bpy.types.ShaderNodeGroup:
                        continue
                    if type(node.node_tree) != bpy.types.ShaderNodeTree:
                        continue                    

                    if node.node_tree.name == node_group_name:
                        has_group = True
                        rewire_from_bsdf_to_bake_node(bake_node_group,mat)

                if has_group == False:
                    has_errors = True
                    message = f'Material {mat.name} does not have {node_group_name} node group.'
                    self.report({"WARNING"}, message=message)


        #Store property with rotation
        for obj in objects_rendered:
            obj.hide_render = False
                
            if lr_cam_bake.get('normal_fix_rotation'):
                obj.lr_render2texture['obj_z_rotation'] = obj.matrix_world.to_euler('XYZ')[2]
            else:
                obj.lr_render2texture['obj_z_rotation'] = 0.0

    
            if lr_cam_bake.get('normal_fix_scale'):
                for i in range(3):
                    obj.lr_render2texture['obj_scale'][i] = obj.matrix_world.to_scale()[i] 
            else:
                attr_scale = obj.lr_render2texture.get('obj_scale')
                if attr_scale:
                    for i in range(3):
                        obj.lr_render2texture['obj_scale'][i] = 1.0   







        store_vis_on_ignored_objs = []
        for obj in objs_disabled: #Hide objects which are not in collection
            store_vis_on_ignored_objs.append((obj,obj.hide_render))
            obj.hide_render = True
        



        # #Store object rotation
        # mf_bake = bpy.data.node_groups.get(node_group_name)
        # materials_with_mf_bake = []
        # for material in bpy.data.materials:
        #     if material.node_tree:  #Loop materials
        #         for mat_nodetree in material.node_tree.nodes: #Loop nodes in material
        #             if mat_nodetree.type == 'GROUP' and len(mat_nodetree.inputs) > 0: #Check for empty node tree 
        #                 if mat_nodetree.node_tree.name:
        #                     if mat_nodetree.node_tree.name == node_group_name:
        #                         materials_with_mf_bake.append(material)



        # # Iterate through all objects in the scene
        # objs_with_mf_bake =[]
        # for obj in bpy.context.scene.objects:
        #     # Check if the object has a material
        #     if obj.type == 'MESH' and obj.data.materials:
        #         # Iterate through all materials of the object
        #         for material_slot in obj.material_slots:
        #             material = material_slot.material
        #             # Check if the material name matches the target material name
        #             if material in materials_with_mf_bake:
                        
        #                 objs_with_mf_bake.append(obj) 
        
        #Disable in render if object is not in proper collection and store its value


        #Store
        original_filepath = bpy.context.scene.render.filepath

        store_color_management = active_scene.render.image_settings.color_management
        store_display_device = active_scene.render.image_settings.display_settings.display_device
        view_store = active_scene.render.image_settings.view_settings.view_transform
        
        #Store render settings
        store_render_engine = active_scene.render.engine #'CYCLES', 'BLENDER_EEVEE'
        store_samples = active_scene.cycles.samples

        #Store render resolution
        resolution_x = active_scene.render.resolution_x
        resolution_y = active_scene.render.resolution_y

        store_format = active_scene.render.image_settings.file_format
        store_device = active_scene.cycles.device

        #Store dither
        store_dither = active_scene.render.dither_intensity
        active_scene.render.dither_intensity = 0

        def bake(active_scene,
                 film_transparency = None,
                 background_color = (0,0,0,1),
                 color_mode = 'RGBA', #Output image mode BW, RGB, RGBA
                 image_suffix = '' ,
                 image_name = 'ImageRender',
                 image_format = 'PNG', #Needs to be packed anyway afterwards so some extra free space is cool
                 display_device ='sRGB', #Not needed with blender 4.0, Does not affect output image... ?
                 view = 'Standard',
                 render_denoise = None,
                 adaptive_sampling = False,
                 render_max_samples= None,
                 render_engine= 'CYCLES',
                 resolution_x = 1024,
                 resolution_y = 1024,
                 sample_clamp_indirect = None,
                 pixel_filter_type = None,
                 render_name = None,
                 transparent_bounces = None): #For debug only
            
            start_time_single = timeit.default_timer()
            if color_mode != None:
                store_color_mode = active_scene.render.image_settings.color_mode
                active_scene.render.image_settings.color_mode = color_mode

            if film_transparency != None:
                film_transparency_store = active_scene.render.film_transparent
                active_scene.render.film_transparent = film_transparency
            
            if sample_clamp_indirect != None:
                store_sample_clamp_indirect = active_scene.cycles.sample_clamp_indirect
                active_scene.cycles.sample_clamp_indirect = sample_clamp_indirect

            if adaptive_sampling != None:
                adaptive_sampling_store = active_scene.cycles.use_adaptive_sampling
                active_scene.cycles.use_adaptive_sampling = adaptive_sampling

            if render_max_samples != None:
                render_max_samples_store = active_scene.cycles.samples
                active_scene.cycles.samples = render_max_samples
            
            if render_denoise != None:
                render_denoise_store = active_scene.cycles.use_denoising
                active_scene.cycles.use_denoising = render_denoise

            if background_color != None:
                background_color_store_R, background_color_store_G, background_color_store_B, background_color_store_A = active_scene.world.node_tree.nodes["Background"].inputs[0].default_value
                active_scene.world.node_tree.nodes["Background"].inputs[0].default_value = background_color

            if pixel_filter_type != None:
                pixel_filter_type_store = active_scene.cycles.pixel_filter_type
                active_scene.cycles.pixel_filter_type = pixel_filter_type

            if transparent_bounces != None:
                transparent_bounces_store = active_scene.cycles.min_transparent_bounces = 18
                active_scene.cycles.min_transparent_bounces = transparent_bounces

            active_scene.render.engine = render_engine
            
            active_scene.render.image_settings.display_settings.display_device = display_device
            active_scene.render.image_settings.view_settings.view_transform = view
    
            bpy.context.scene.render.filepath = '//RenderOutput/' + 'T_' + image_name + image_suffix +'.'+ image_format
            
            active_scene.render.resolution_x = resolution_x
            active_scene.render.resolution_y = resolution_y
            a,b,c,d = active_scene.world.node_tree.nodes["Background"].inputs[0].default_value
            print(f'------------------\n')
            if film_transparency == True:
                rep_bcg = 'Transparent'
            else:
                rep_bcg = f'R:{a} G:{b} B:{c} A:{d}'

            print(f'RENDERING: {render_name}\n\nFilm Transparency: {film_transparency}\nBackground Color: {rep_bcg}\nDenoise: {render_denoise}\nSamples: {render_max_samples}\nView Transform: {view}\nDisplay Device: {display_device}\nPixel Filter Type: {pixel_filter_type}\nColor Mode\Texture Channels: {color_mode}\n')

            bpy.ops.render.render(write_still=True)

            print(f'------------------\n\n')



            #Restore render settings
            if render_denoise != None:
                active_scene.cycles.use_denoising = render_denoise_store

            if color_mode != None:
                active_scene.render.image_settings.color_mode = store_color_mode
                
            if film_transparency != None:
                active_scene.render.film_transparent = film_transparency_store

            if adaptive_sampling != None:
                active_scene.cycles.use_adaptive_sampling = adaptive_sampling_store
                
            if render_max_samples != None:
                active_scene.cycles.samples = render_max_samples_store

            if sample_clamp_indirect != None:
                active_scene.cycles.sample_clamp_indirect = store_sample_clamp_indirect
            
            if pixel_filter_type != None:
                active_scene.cycles.pixel_filter_type = pixel_filter_type_store

            if background_color != None:
                active_scene.world.node_tree.nodes["Background"].inputs[0].default_value = (background_color_store_R, background_color_store_G, background_color_store_B, background_color_store_A)
            if transparent_bounces != None:

                active_scene.cycles.min_transparent_bounces = transparent_bounces_store




        active_scene.render.image_settings.file_format = 'TARGA'
        active_scene.render.image_settings.color_management = 'OVERRIDE'

        if lr_cam_bake.render_device == 'OP1':
            active_scene.cycles.device = 'CPU'
        elif lr_cam_bake.render_device == 'OP2':
            active_scene.cycles.device = 'GPU'

        # -------------- LOOPING OVER MG OUTPUTS AND RENDERING EACH --------------
        current_render = 0
        
        for output in mf_outputs:
            output.is_active_output = True

            # if lr_cam_bake.get('render_albedo'):
            if lr_cam_bake.albedo_render:
                if output.name == 'Albedo':
                    bake(active_scene= active_scene,
                        film_transparency= True,
                        image_suffix= '_A',
                        background_color=(0,0,0,1),
                        image_name= image_name,
                        image_format= image_format,
                        #  display_device = 'sRGB',
                        view = 'Standard',
                        resolution_x=lr_cam_bake.resolution_x,
                        resolution_y=lr_cam_bake.resolution_y,
                        
                        render_denoise=False,
                        adaptive_sampling = False,
                        render_max_samples= lr_cam_bake.get('albedo_render_samples') if lr_cam_bake.get('albedo_render_samples') else 1,
                        pixel_filter_type = 'BOX',
                        render_name = 'Albedo',
                        transparent_bounces=5)
            
            # if lr_cam_bake.get('render_alpha'):
            if lr_cam_bake.render_alpha:
                if output.name == 'Alpha':
                    bake(active_scene= active_scene,
                         color_mode = 'RGB',
                         film_transparency= False,
                         image_suffix= '_K',
                         background_color=(0,0,0,1),
                         image_name= image_name,
                         image_format= image_format,
                         #  display_device = 'None', 
                         view = 'Raw',
                         resolution_x=lr_cam_bake.resolution_x,
                         resolution_y=lr_cam_bake.resolution_y,
                         
                         render_denoise=False,
                         adaptive_sampling = False,
                         render_max_samples= lr_cam_bake.get('render_alpha_samples') if lr_cam_bake.get('render_alpha_samples') else 1,
                         pixel_filter_type = 'BOX',
                         render_name = 'Alpha')   
            
            # if lr_cam_bake.get('render_normal'):
            if lr_cam_bake.render_normal:
                if output.name == 'Normal':
                    bake(active_scene= active_scene,
                         color_mode = 'RGBA',
                         film_transparency= True,
                         image_suffix= '_N',
                         background_color=(0.5,0.5,1,1),
                         image_name= image_name,
                         image_format= image_format,
                         #  display_device = 'None',
                         view = 'Raw',
                         resolution_x=lr_cam_bake.resolution_x,
                         resolution_y=lr_cam_bake.resolution_y,
                         
                         render_denoise=False,
                         adaptive_sampling = False,
                         render_max_samples = lr_cam_bake.get('normal_render_samples') if lr_cam_bake.get('normal_render_samples') else 1,
                         pixel_filter_type = 'BOX',
                         render_name = 'Normal',
                         transparent_bounces=5)
            
            # if lr_cam_bake.get('render_ao'):
            if lr_cam_bake.render_ao:
                if output.name == 'Occlusion_Texture':
                    bake(active_scene= active_scene,
                        film_transparency= True,
                        image_suffix= '_O',
                        background_color=(1,1,1,1),
                        image_name= image_name,
                        image_format= image_format,
                        #  display_device = 'None', 
                        view = 'Raw',
                        resolution_x=lr_cam_bake.resolution_x,
                        resolution_y=lr_cam_bake.resolution_y,
                        
                        render_denoise=False,
                        adaptive_sampling = False,
                        render_max_samples= 1,
                        pixel_filter_type = 'BOX',
                        render_name = 'AO',
                        transparent_bounces=5)   
            
            # if lr_cam_bake.get('render_ao_scene'): 
            if lr_cam_bake.render_ao_scene: 
                if output.name == 'Occlusion_Scene':
                    bake(active_scene= active_scene,
                         film_transparency= True,
                         image_suffix= '_Scene_O',
                         background_color=(1,1,1,1), 
                         image_name = image_name, 
                         image_format = image_format, 
                         #  display_device = 'None',
                         resolution_x = lr_cam_bake.resolution_x,
                         resolution_y = lr_cam_bake.resolution_y,
 
                         render_denoise=lr_cam_bake.render_ao_denoise,
                         render_max_samples= lr_cam_bake.render_ao_denoise_samples,
                         adaptive_sampling = False,
                         sample_clamp_indirect = 0.0001,
                         pixel_filter_type = 'BOX',
                         render_name = 'AO Scene',
                         transparent_bounces=5)   
            
            # if lr_cam_bake.get('render_ao_scene'): 
            if lr_cam_bake.render_ao_material: 
                if output.name == 'Occlusion_Material':
                    bake(active_scene= active_scene,
                         film_transparency= True,
                         image_suffix= '_Material_O',
                         background_color=(1,1,1,1), 
                         image_name = image_name, 
                         image_format = image_format, 
                         #  display_device = 'None',
                         resolution_x = lr_cam_bake.resolution_x,
                         resolution_y = lr_cam_bake.resolution_y,
 
                         render_denoise=lr_cam_bake.render_ao_denoise,
                         render_max_samples= lr_cam_bake.render_ao_denoise_samples,
                         adaptive_sampling = False,
                         sample_clamp_indirect = None,
                         pixel_filter_type = 'BOX',
                         render_name = 'AO Material',
                         transparent_bounces=5)   



        
            # if lr_cam_bake.get('render_roughness'):
            if lr_cam_bake.render_roughness:
                if output.name == 'Roughness':
                    bake(active_scene= active_scene,
                        film_transparency= True,
                        image_suffix= '_R',
                        background_color=(0,0,0,1),
                        image_name= image_name,
                        image_format= image_format,
                        #  display_device = 'None',
                        view = 'Raw',
                        resolution_x=lr_cam_bake.resolution_x,
                        resolution_y=lr_cam_bake.resolution_y,

                        render_denoise=False,
                        adaptive_sampling = False,
                        render_max_samples=1,
                        pixel_filter_type = 'BOX',
                        render_name = 'Roughness',
                        transparent_bounces=5)   
                
            # if lr_cam_bake.get('render_metallic'):
            if lr_cam_bake.render_metallic:
                if output.name == 'Metallic':
                    bake(active_scene= active_scene,
                        film_transparency= True,
                        image_suffix= '_M',
                        background_color=(0,0,0,1),
                        image_name= image_name,
                        image_format= image_format,
                        #Display_device = 'None',
                        view = 'Raw',
                        resolution_x=lr_cam_bake.resolution_x,
                        resolution_y=lr_cam_bake.resolution_y,
                        
                        render_denoise=False,
                        adaptive_sampling = False,
                        render_max_samples=1,
                        pixel_filter_type = 'BOX',
                        render_name = 'Metallic',
                        transparent_bounces=5)
            
            # if lr_cam_bake.get('render_height'):
            if lr_cam_bake.render_height:
                if output.name == 'Height':
                    bake(active_scene= active_scene,
                         film_transparency= False,
                         image_suffix= '_H',
                         background_color=(0.5,0.5,0.5,1),
                         image_name= image_name,
                         image_format= image_format_height,
                         #  display_device = 'None',
                         view = 'Raw',
                         resolution_x=lr_cam_bake.resolution_x,
                         resolution_y=lr_cam_bake.resolution_y,
                         render_denoise=False,
                         adaptive_sampling = False,
                         render_max_samples= 1,
                         pixel_filter_type = 'BOX',
                         render_name = 'Height')   
            

  
        #Restore to original filepath
        bpy.context.scene.render.filepath = original_filepath
 
        #Restore display_device settings
        active_scene.render.image_settings.color_management= store_color_management
        active_scene.render.image_settings.display_settings.display_device = store_display_device
        active_scene.render.image_settings.view_settings.view_transform = view_store

        #Restore render settings
        active_scene.render.engine = store_render_engine

        #Restore render resolution
        active_scene.render.resolution_x = resolution_x
        active_scene.render.resolution_y = resolution_y

        #Restore dither
        active_scene.render.dither_intensity = store_dither


        active_scene.render.image_settings.file_format = store_format


        active_scene.cycles.device = store_device


        #restore render visibility



        for idx in objects_eval:
            objects_eval[idx]['obj'].hide_render = objects_eval[idx]['render_visibility_init']  


        bpy.ops.object.select_all(action='DESELECT')        
        #Delete flattened objects
        flattened_objects.extend(empty_leftover)

        for obj in flattened_objects:
            obj.select_set(True)            
        bpy.ops.object.delete()


        bpy.ops.object.select_all(action='DESELECT')
        #Restore obj selections
        for obj in store_obj_selection:
            obj.select_set(True)
            
        bpy.context.view_layer.objects.active = store_obj_active
        # print(f'{store_vis_on_ignored_objs= }')
        #Restore render visibility on objects outside of collection
        for obj in store_vis_on_ignored_objs:
            obj[0].hide_render = obj[1]

        # message = f'{(current_render+1)} of {len(mf_outputs)} done.'
        elapsed_time = timeit.default_timer() - start_time
        
        if has_errors == True:
            message = f'Time: {elapsed_time:.2f}s. With Errors.'
            self.report({"WARNING"}, message=message)
        else:
            message = f'Time: {elapsed_time:.2f}s.'
            self.report({"INFO"}, message=message)
        
        

    
        return {'FINISHED'}





