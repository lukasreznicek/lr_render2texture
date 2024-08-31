# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import bpy

bl_info = {
    "name" : "LR Render 2 Texture",
    "author" : "Lukas Reznicek",
    "description" : "For baking atlas textures with transparency through camera",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}


from bpy.props import IntProperty, CollectionProperty, StringProperty,FloatVectorProperty,BoolProperty,EnumProperty
from .operators.render import LR_TOOLS_OT_R2T_Render,LR_TOOLS_OT_r2t_new_camera,LR_TOOLS_OT_r2t_append_ng

# Properties
# To acess properties: bpy.data.scenes['Scene'].lr_cam_bake
# Is assigned by pointer property below in class registration.


class LR_Render2Texture_Settings(bpy.types.PropertyGroup):
    # add_missing_ng: bpy.props.BoolProperty(name="Add Missing NG",description="Adds node group to a material when rendered object does not have it", default=True)
    

    resolution_x: bpy.props.IntProperty(name="W:", description="Rendered Texture Width", default=2048, min = 4, soft_max = 8192)
    resolution_y: bpy.props.IntProperty(name="H:", description="Rendered Texture Height", default=2048, min = 4, soft_max = 8192)
    render_device:bpy.props.EnumProperty(name= 'Device', description= '', items= [('OP1', 'CPU',''),('OP2', 'GPU','')])
    render_ao_denoise: bpy.props.BoolProperty(name="Use denoise on AO render", default=True)
    render_ao_denoise_samples: bpy.props.IntProperty(name="AO Scene Render Samples", description="", default=50, min = 1, soft_max = 200)
    export_path:bpy.props.StringProperty(name="Export Path", description="// = .blend file location\n//..\ = .blend file parent folder", default="//RenderOutput/", maxlen=1024,subtype='DIR_PATH')
    img_name:bpy.props.StringProperty(name="Texture Name", description="Name of the rendered image", default="ImageRender")    
    img_height_suffix:bpy.props.StringProperty(name="Suffix", description="", default="_H")
    # coll_ptr: bpy.props.PointerProperty(name="Collection", type=bpy.types.Collection, description="Only Objects in this collection will be rendered")
    
    
    render_normal: bpy.props.BoolProperty(name="Render Height Texture Input", default=False, description='Normal Texture input into function\nNormal texture straight into node group. Do not add NormalMap node after texture')
    normal_combine: bpy.props.BoolProperty(name="Add Geometry Normal", default=True, description='Combine texture input normal with geometry normal\n if thexture input is empty, output is geometry normal only')
    # render_normal_inpaint: bpy.props.BoolProperty(name="Inpaint", default=True, description='Postprocessing inpaint')

    normal_render_samples: bpy.props.IntProperty(default=1, min = 1, soft_max = 512, name="Normal Samples", description="Number of rays per pixel.\n1 is fine but aliasing could be achieved with more samples per pixel. 10 should be fine for removing aliasing")
    normal_fix_rotation: bpy.props.BoolProperty(name='Rotation Fix',description="Normal map texture source rotation will be adjusted based on object rotation and baked. Will not work with applied rotation on an object", default=False)
    normal_fix_scale: bpy.props.BoolProperty(name='Scale Fix',description="Normal map intensity will be scaled based on object scale", default=False)



    albedo_render: bpy.props.BoolProperty(name="Render Base Color Texture Input", default=False)
    albedo_render_samples: bpy.props.IntProperty(name="Samples", default=1)



    render_ao: bpy.props.BoolProperty(name="Render AO Texture Input", default=False)
    
    render_ao_film_transparency: bpy.props.BoolProperty(name='Film Transparent',description="Use Transparent background Instead", default=False)
    render_ao_scene: bpy.props.BoolProperty(name="Render AO Scene", default=False, description='AO Bake from scene')
    render_ao_material: bpy.props.BoolProperty(name="Render AO Material", default=False, description='Ambient Occlusion from material node. Does not work with transparency')
    # render_ao_material_only_local: bpy.props.BoolProperty(name="Render AO Material", default=False, description='Only consider the object itself when computing AO')

    render_roughness: bpy.props.BoolProperty(name="Render Roughness Texture Input", default=False)
    
    # #Post process
    # post_inpaint: bpy.props.BoolProperty(name="Inpaint", default = True)


    render_metallic: bpy.props.BoolProperty(name="Render Metallic Texture Input", default=False)
    render_height: bpy.props.BoolProperty(name="Render Height Texture Input", default=False)

    render_alpha: bpy.props.BoolProperty(name="Render Alpha Texture Input ", default=False)
    render_alpha_samples: bpy.props.IntProperty(default=1, min = 1, soft_max = 512, name="Alpha Samples", description="Number of rays per pixel.\n1 is fine but aliasing could be achieved with more samples per pixel. 10 should be fine for removing aliasing")

        
    bdrop_color_height: bpy.props.FloatVectorProperty(
        name="Bdrop Color",
        subtype='COLOR',
        size=4,  # RGB values
        default=(0.0, 0.0, 0.0, 1.0),  # Default white color
        min=0.0,
        max=1.0
    )

class LR_Render2Texture_Settings_Object(bpy.types.PropertyGroup):
        # obj_render: bpy.props.BoolProperty(name="RenderObject",default=False)
        obj_z_rotation: bpy.props.FloatProperty(name="Object_Z_Rotation",default=0.0)
        obj_scale: bpy.props.FloatVectorProperty(name="Object_Scale",default=(1.0,1.0,1.0))
        
        object_mode:bpy.props.EnumProperty(
            name="Export mode",
            description="Export mode",
            override={'LIBRARY_OVERRIDABLE'},
            items=[
                ("RENDERED", "Rendered", "Object is included in export if in hierarchy.","CHECKMARK",1),
                # ("PARENT","Export recursive","Export this object and its children","KEYINGSET",2),
                ("NOT_RENDERED","Ignored","Object Is Not visible In Render","X",2)],
                default="NOT_RENDERED"
        )

#UI -------------------------------------------------------------------------------------

class VIEW3D_PT_lr_Render2Texture_setup(bpy.types.Panel):
    bl_label = "R2T"
    bl_idname = "OBJECT_PT_lr_bake_setup"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'   
    bl_category = 'LR R2T'

    # @classmethod
    # def poll(cls, context):
    #     # return context.active_object is not None
    #     return True 
    
    # def draw(self, context):

    def draw(self, context):

        
        lr_render2texture = context.scene.lr_render2texture
        # 

        cam_obj = bpy.data.objects.get('LR_RenderToTexture')
        
        if (cam_obj != None and cam_obj.type != 'CAMERA') or (cam_obj == None):
            layout = self.layout.box()
            row = layout.row(align=True)
            row.operator("lr_tools.r2t_new_camera", text="Add Cam", icon = 'CAMERA_DATA')
            row.scale_y = 2
            return 
        


        layout = self.layout.box()
        layout.label(text='Scene Settings:')

        # layout.label(text="Render")
        row = layout.row(align=True)
        row.prop(lr_render2texture, 'img_name')

        row = layout.row(align=True)
        row.prop(lr_render2texture, "resolution_x")
        row.prop(lr_render2texture, "resolution_y")
        # row = layout.row(align=True)
        
        row = layout.row(align=True)
        row.prop(lr_render2texture, 'render_device')


        row = layout.row(align=True)
        row.prop(lr_render2texture, 'export_path')


        # layout = self.layout.box()
        # layout.label(text='PostPro Settings:')



            



        # header, panel = layout.panel("settings_inpaint", default_closed=False)
        # header.label(text="Inpaint")
        # if panel:
        #     lr_render2texture = context.scene.lr_render2texture
        #     panel.prop(lr_render2texture, "post_inpaint")


        layout = self.layout.box()
        layout.label(text='Object Settings:')

        lr_render2texture_obj = context.object.lr_render2texture
        row = layout.row(align=True)
        row.prop(lr_render2texture_obj, 'object_mode', text ='Object Mode', icon='OBJECT_DATA', expand=True, icon_only =False)



        layout = self.layout.box()
        layout.label(text='Textures to render:')
        collumn_f = layout.column_flow(columns=2, align=True)
        collumn_f.prop(lr_render2texture, "albedo_render", text="Base Color")
        collumn_f.prop(lr_render2texture, "render_alpha", text="Alpha")
        collumn_f.prop(lr_render2texture, "render_normal", text="Normal")
        collumn_f.prop(lr_render2texture, "render_ao", text="AO")
        collumn_f.prop(lr_render2texture, "render_roughness", text="Roughness")
        collumn_f.prop(lr_render2texture, "render_metallic", text="Metallic")
        collumn_f.prop(lr_render2texture, "render_height", text="Height")
        collumn_f.prop(lr_render2texture, "render_ao_scene", text="AO Scene")
        collumn_f.prop(lr_render2texture, "render_ao_material", text="AO Material")
        


        layout = self.layout.box()
        row = layout.row(align=True)
        row.operator("lr_tools.r2t_new_camera", text="Add Cam", icon = 'CAMERA_DATA')
        row.operator("lr_tools.r2t_append_ng", text="Add MF", icon = 'NODE_MATERIAL')

        row = layout.row(align=True)
        row.scale_y = 2  # Increase the height
        op = row.operator("lr_tools.r2t_render", text="Render", icon = 'EXPORT')

        layout = self.layout
        scene = context.scene

        # layout.label(text="Render Settings")

        lr_render2texture = context.scene.lr_render2texture
        
        if context.scene.lr_render2texture.render_alpha:
            header, panel = layout.panel("settings_alpha", default_closed=True)
            header.label(text="Alpha")
            if panel:
                # row = layout.row(align=True)
                panel.prop(lr_render2texture, 'render_alpha_samples')

        if context.scene.lr_render2texture.render_ao_scene:
            header, panel = layout.panel("settings_ao_scene", default_closed=False)
            header.label(text="AO Scene")
            if panel:
                lr_render2texture = context.scene.lr_render2texture
                # row = layout.row(align=True)
                panel.prop(lr_render2texture, 'render_ao_denoise_samples')
                panel.prop(lr_render2texture, 'render_ao_denoise')
                panel.prop(lr_render2texture, 'render_ao_film_transparency')




        if context.scene.lr_render2texture.render_normal:
            header, panel = layout.panel("settings_normal", default_closed=True)
            header.label(text="Normal")
            if panel:
                lr_render2texture = context.scene.lr_render2texture
                # row = layout.row(align=True)
                panel.prop(lr_render2texture, 'normal_combine')
                # panel.prop(lr_render2texture, 'render_normal_inpaint')
                panel.prop(lr_render2texture, 'normal_render_samples')
                panel.prop(lr_render2texture, 'normal_fix_rotation')
                panel.prop(lr_render2texture, 'normal_fix_scale')


        if context.scene.lr_render2texture.albedo_render:
            header, panel = layout.panel("color_settings", default_closed=True)
            header.label(text="Base Color")
            if panel:
                lr_render2texture = context.scene.lr_render2texture
                # row = layout.row(align=True)
                panel.prop(lr_render2texture, 'albedo_render_samples')






        

classes = (LR_Render2Texture_Settings,
           LR_Render2Texture_Settings_Object,

           VIEW3D_PT_lr_Render2Texture_setup,
        #    VIEW3D_PT_lr_Render2Texture_normal,
        #    VIEW3D_PT_lr_Render2Texture_alpha,
        #    VIEW3D_PT_lr_Render2Texture_ao_scene,

           LR_TOOLS_OT_R2T_Render,
           LR_TOOLS_OT_r2t_new_camera,
           LR_TOOLS_OT_r2t_append_ng)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.lr_render2texture = bpy.props.PointerProperty(type=LR_Render2Texture_Settings)
    bpy.types.Object.lr_render2texture = bpy.props.PointerProperty(type=LR_Render2Texture_Settings_Object)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.lr_render2texture
    del bpy.types.Object.lr_render2texture
