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


addon_name = 'lr_cam_bake'



from bpy.props import IntProperty, CollectionProperty, StringProperty,FloatVectorProperty,BoolProperty,EnumProperty
from .operators.render import LR_TOOLS_OT_r2t_cam_bake,LR_TOOLS_OT_r2t_new_camera,LR_TOOLS_OT_r2t_append_mg

# Properties 
# To acess properties: bpy.data.scenes['Scene'].lr_cam_bake
# Is assigned by pointer property below in class registration.
class LR_CamBake_Settings(bpy.types.PropertyGroup):
    # add_missing_mg: bpy.props.BoolProperty(name="Add Missing MG",description="Adds material group to a material when rendered object does not have it", default=True)

    resolution_x: bpy.props.IntProperty(name="W:", description="Rendered Texture Width", default=2048, min = 4, soft_max = 8192)
    resolution_y: bpy.props.IntProperty(name="H:", description="Rendered Texture Height", default=2048, min = 4, soft_max = 8192)
    render_device:bpy.props.EnumProperty(name= 'Device', description= '', items= [('OP1', 'CPU',''),('OP2', 'GPU','')])
    render_ao_denoise: bpy.props.BoolProperty(name="Use denoise on AO render", default=True)
    render_ao_denoise_samples: bpy.props.IntProperty(name="AO Scene Render Samples", description="", default=50, min = 1, soft_max = 200)
    export_path:bpy.props.StringProperty(name="Export Path", description="// = .blend file location\n//..\ = .blend file parent folder", default="//RenderOutput/", maxlen=1024,subtype='DIR_PATH')
    img_name:bpy.props.StringProperty(name="Texture Name", description="Name of the rendered image", default="ImageRender")    
    img_height_suffix:bpy.props.StringProperty(name="Suffix", description="", default="_H")
    coll_ptr: bpy.props.PointerProperty(name="Collection", type=bpy.types.Collection, description="Only Objects in this collection will be rendered")
    
    
    render_normal: bpy.props.BoolProperty(name="Render Height Texture Input", default=False, description='Normal Texture input into function\nNormal texture straight into node group. Do not add NormalMap node after texture')
    render_normal_combined: bpy.props.BoolProperty(name="Render Height Texture Input", default=True, description='Normal Texture function input + Geometry Normal\nNormal texture straight into node group. Do not add NormalMap node after texture\n\nIf only Geometry normals are needed, leave normal map empty in node group')
    render_normal_samples: bpy.props.IntProperty(default=1, min = 1, soft_max = 512, name="Normal Samples", description="Number of rays per pixel.\n1 is fine but aliasing could be achieved with more samples per pixel. 10 should be fine for removing aliasing")
    normal_fix_rotation: bpy.props.BoolProperty(name='Rotation Fix',description="Normal map texture source rotation will be adjusted based on object rotation and baked", default=False)
    normal_fix_scale: bpy.props.BoolProperty(name='Scale Fix',description="Normal map intensity will be scaled based on object scale", default=False)

    render_albedo: bpy.props.BoolProperty(name="Render Albedo Texture Input", default=False)

    render_ao: bpy.props.BoolProperty(name="Render AO Texture Input", default=False)
    render_ao_film_transparency: bpy.props.BoolProperty(name='Film Transparent',description="Use Transparent background Instead", default=False)

    render_roughness: bpy.props.BoolProperty(name="Render Roughness Texture Input", default=False)
    render_metallic: bpy.props.BoolProperty(name="Render Metallic Texture Input", default=False)
    render_height: bpy.props.BoolProperty(name="Render Height Texture Input", default=False)
    render_ao_scene: bpy.props.BoolProperty(name="Render AO Scene", default=False, description='AO Bake from scene')
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

class LR_CamBake_Settings_Object(bpy.types.PropertyGroup):
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

class VIEW3D_PT_lr_cam_bake_setup(bpy.types.Panel):
    bl_label = "R2T"
    bl_idname = "OBJECT_PT_lr_bake_setup"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LR R2T'
            

    def draw(self, context):
        
        lr_cam_bake = context.scene.lr_cam_bake
        lr_cam_bake_obj = context.object.lr_cam_bake_obj

        layout = self.layout.box()
        layout.label(text='Scene Settings:')


        # layout.label(text="Render")
        row = layout.row(align=True)
        row.prop(lr_cam_bake, 'img_name')

        row = layout.row(align=True)
        row.prop(lr_cam_bake, "resolution_x")
        row.prop(lr_cam_bake, "resolution_y")
        # row = layout.row(align=True)
        
        row = layout.row(align=True)
        row.prop(lr_cam_bake, 'render_device')


        row = layout.row(align=True)
        row.prop(lr_cam_bake, 'export_path')

        # row = layout.row(align=True)
        # row.prop(lr_cam_bake, 'add_missing_mg')
        # row = layout.row(align=True)
        # row.scale_y = 1  # Increase the height
        # row.prop(lr_cam_bake, "coll_ptr", text="Collection")

        layout = self.layout.box()
        layout.label(text='Object Settings:')

        row = layout.row(align=True)
        row.prop(lr_cam_bake_obj, 'object_mode', text ='Object Mode', icon='OBJECT_DATA', expand=True, icon_only =False)


        layout = self.layout.box()
        layout.label(text='Textures to render:')
        collumn_f = layout.column_flow(columns=2, align=True)
        collumn_f.prop(lr_cam_bake, "render_albedo", text="Albedo")
        collumn_f.prop(lr_cam_bake, "render_normal", text="Normal")
        collumn_f.prop(lr_cam_bake, "render_normal_combined", text="Normal Combined")
        collumn_f.prop(lr_cam_bake, "render_ao", text="AO")
        collumn_f.prop(lr_cam_bake, "render_roughness", text="Roughness")
        collumn_f.prop(lr_cam_bake, "render_metallic", text="Metallic")
        collumn_f.prop(lr_cam_bake, "render_height", text="Height")
        collumn_f.prop(lr_cam_bake, "render_ao_scene", text="AO Scene")
        collumn_f.prop(lr_cam_bake, "render_alpha", text="Alpha")

        layout = self.layout.box()
        row = layout.row(align=True)
        row.operator("lr_tools.r2t_new_camera", text="Add Cam", icon = 'CAMERA_DATA')
        row.operator("lr_tools.r2t_append_mg", text="Add MF", icon = 'NODE_MATERIAL')

        row = layout.row(align=True)
        row.scale_y = 2  # Increase the height
        op = row.operator("lr_tools.r2t_cam_bake", text="Render", icon = 'EXPORT')


class VIEW3D_PT_lr_cam_bake_alpha(bpy.types.Panel):
    bl_label = "Alpha Texture"
    bl_idname = "OBJECT_PT_lr_render_alpha"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LR R2T'
    bl_parent_id = "OBJECT_PT_lr_bake_setup"
        
    @classmethod
    def poll(cls, context):
        return context.scene.lr_cam_bake.render_alpha

    def draw(self, context):
        lr_cam_bake = context.scene.lr_cam_bake

        layout = self.layout.box()
        row = layout.row(align=True)
        row.prop(lr_cam_bake, 'render_alpha_samples')

class VIEW3D_PT_lr_cam_bake_ao_scene(bpy.types.Panel):
    bl_label = "AO Scene"
    bl_idname = "OBJECT_PT_lr_bake_ao_scene"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LR R2T'
    bl_parent_id = "OBJECT_PT_lr_bake_setup"
        
    @classmethod
    def poll(cls, context):
        return context.scene.lr_cam_bake.render_ao_scene

    def draw(self, context):
        lr_cam_bake = context.scene.lr_cam_bake

        layout = self.layout.box()
        row = layout.row(align=True)

        row = layout.row(align=True)
        row.prop(lr_cam_bake, 'render_ao_denoise_samples')
        row.prop(lr_cam_bake, 'render_ao_denoise')
        row = layout.row(align=True)
        row.prop(lr_cam_bake, 'render_ao_film_transparency')
    
class VIEW3D_PT_lr_cam_bake_normal(bpy.types.Panel):
    bl_label = "Normal"
    bl_idname = "OBJECT_PT_lr_bake_normal"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LR R2T'
    bl_parent_id = "OBJECT_PT_lr_bake_setup"
        
    @classmethod
    def poll(cls, context):

        if context.scene.lr_cam_bake.render_normal or context.scene.lr_cam_bake.render_normal_combined:
            ret =  True
        else:
            ret = False
        return ret

    def draw(self, context):
        lr_cam_bake = context.scene.lr_cam_bake

        layout = self.layout.box()
        row = layout.row(align=True)
        row.prop(lr_cam_bake, 'render_normal_samples')
        row = layout.row(align=True)
        row.prop(lr_cam_bake, 'normal_fix_rotation')
        row.prop(lr_cam_bake, 'normal_fix_scale')
        

classes = (LR_CamBake_Settings,
           LR_CamBake_Settings_Object,

           VIEW3D_PT_lr_cam_bake_setup,
           VIEW3D_PT_lr_cam_bake_normal,
           VIEW3D_PT_lr_cam_bake_alpha,
           VIEW3D_PT_lr_cam_bake_ao_scene,

           LR_TOOLS_OT_r2t_cam_bake,
           LR_TOOLS_OT_r2t_new_camera,
           LR_TOOLS_OT_r2t_append_mg)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.lr_cam_bake = bpy.props.PointerProperty(type=LR_CamBake_Settings)
    bpy.types.Object.lr_cam_bake_obj = bpy.props.PointerProperty(type=LR_CamBake_Settings_Object)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.lr_cam_bake
    del bpy.types.Object.lr_cam_bake_obj
