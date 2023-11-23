import bpy
from functions import bake,get_material_group_outputs

class OBJECT_OT_lr_cam_bake_height(bpy.types.Operator):
    bl_idname = "object.lr_cam_bake_height"
    bl_label = "Bake Height From Active Camera"
    bl_options = {'REGISTER', 'UNDO'}


    
    def execute(self, context): 

        # Name of the node group
        active_scene = bpy.context.scene
        lr_cam_bake_settings = active_scene.lr_cam_bake
        node_group_name = "MF_LR_Bake_Input"
        image_name = lr_cam_bake_settings.img_name
        image_format = 'TGA'
        image_format_height = 'OPEN_EXR'

        bcg_color= active_scene.world.node_tree.nodes["Background"].inputs[0].default_value


        if bpy.data.is_saved == False:
            message = 'File needs to be saved. Exitting.'
            self.report({'ERROR'}, message)
            return {'CANCELLED'}           




        #Store

        original_filepath = bpy.context.scene.render.filepath

        
        
        
        #Store render settings
        store_render_engine = active_scene.render.engine #'CYCLES', 'BLENDER_EEVEE'





        store_device = active_scene.cycles.device
        store_film_transparency = active_scene.render.film_transparent

        
        mf_check = False
        for mf in bpy.data.node_groups:
            if mf.name == 'MF_LR_Bake_Input':
                mf_check = True
                mf_outputs = get_material_group_outputs(node_group_name)
                
        if mf_check == False:
            message = f'Scene needs to have {node_group_name}'
            self.report({'ERROR'}, message)
            return {'CANCELLED'}               





        active_scene.render.image_settings.file_format = 'TARGA'
        active_scene.render.image_settings.color_management = 'OVERRIDE'
        active_scene.render.film_transparent = True

        if lr_cam_bake_settings.render_device == 'OP1':
            active_scene.cycles.device = 'CPU'
        elif lr_cam_bake_settings.render_device == 'OP2':
            active_scene.cycles.device = 'GPU'
        

        current_render = 0
        for output in mf_outputs:
            if output.name == 'Height':
                output.is_active_output = True

                bake(world=active_scene.world,
                     image_suffix= '_H',
                     background_color=(0.5,0.5,0.5,1),
                     image_name= image_name,
                     image_format= image_format_height,
                     display_device = 'None',
                     resolution_x=lr_cam_bake_settings.resolution_x,
                     resolution_y=lr_cam_bake_settings.resolution_y,
                     
                     render_denoise=False,
                     render_max_samples= 1)   
            
            # message = f'{(current_render+1)} of {len(mf_outputs)} done.'
            message = f'Height done'
            self.report({"INFO"}, message=message)
  




        #Restore to original filepath
        bpy.context.scene.render.filepath = original_filepath
 
        #Restore display_device settings
        active_scene.render.image_settings.color_management= store_color_management


        #Restore render settings
        active_scene.render.engine = store_render_engine



        active_scene.render.film_transparent = store_film_transparency

        active_scene.cycles.device = store_device
        return {'FINISHED'}





