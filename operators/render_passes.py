import bpy
from .functions import bake,get_material_group_outputs

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
        image_path = lr_cam_bake_settings.export_path


        if bpy.data.is_saved == False:
            message = 'File needs to be saved. Exitting.'
            self.report({'ERROR'}, message)
            return {'CANCELLED'}           

        mf_check = False
        for mf in bpy.data.node_groups:
            if mf.name == 'MF_LR_Bake_Input':
                mf_check = True
                mf_outputs = get_material_group_outputs(node_group_name)
                
        if mf_check == False:
            message = f'Scene needs to have {node_group_name}'
            self.report({'ERROR'}, message)
            return {'CANCELLED'}               


        if lr_cam_bake_settings.render_device == 'OP1':
            render_engine = 'CPU'
        elif lr_cam_bake_settings.render_device == 'OP2':
            render_engine = 'GPU'
        

        for output in mf_outputs:
            if output.name == 'Height':
                output.is_active_output = True

                bake(active_scene = active_scene,
                    background_color = (lr_cam_bake_settings.bdrop_color_height[0],lr_cam_bake_settings.bdrop_color_height[1],lr_cam_bake_settings.bdrop_color_height[2],lr_cam_bake_settings.bdrop_color_height[3]),
                    image_name = 'ImageRender',
                    image_suffix= '_H',
                    image_format = 'TARGA',
                    display_device ='',
                    render_denoise = None,
                    render_max_samples= None,
                    render_engine= render_engine,
                    render_using = None,
                    render_resolution = (1024,1024),
                    sample_clamp_indirect = None,
                    filepath = '//',
                    transparent_bdrop = None) #True,False 


            message = f'Height done'
            self.report({"INFO"}, message=message)
        return {'FINISHED'}





class OBJECT_OT_lr_cam_bake_albedo(bpy.types.Operator):
    bl_idname = "object.lr_cam_bake_albedo"
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
        image_path = lr_cam_bake_settings.export_path


        if bpy.data.is_saved == False:
            message = 'File needs to be saved. Exitting.'
            self.report({'ERROR'}, message)
            return {'CANCELLED'}           

        mf_check = False
        for mf in bpy.data.node_groups:
            if mf.name == 'MF_LR_Bake_Input':
                mf_check = True
                mf_outputs = get_material_group_outputs(node_group_name)
                
        if mf_check == False:
            message = f'Scene needs to have {node_group_name}'
            self.report({'ERROR'}, message)
            return {'CANCELLED'}               


        if lr_cam_bake_settings.render_device == 'OP1':
            render_engine = 'CPU'
        elif lr_cam_bake_settings.render_device == 'OP2':
            render_engine = 'GPU'
        

        for output in mf_outputs:
            if output.name == 'Height':
                output.is_active_output = True

                bake(active_scene = active_scene,
                    background_color = (0,0,0,1),
                    image_name = 'ImageRender',
                    image_suffix= '_H',
                    image_format = 'TARGA',
                    display_device ='',
                    render_denoise = None,
                    render_max_samples= None,
                    render_engine= render_engine,
                    render_using = None,
                    render_resolution = (1024,1024),
                    sample_clamp_indirect = None,
                    filepath = '//',
                    transparent_bdrop = None) #True,False 


            message = f'Height done'
            self.report({"INFO"}, message=message)
        return {'FINISHED'}
