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
    "name" : "LR Camera Bake",
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
from .operators.render import OBJECT_OT_lr_cam_bake
from .operators.render_passes import OBJECT_OT_lr_cam_bake_height,OBJECT_OT_lr_cam_bake_albedo
# Properties 
# To acess properties: bpy.data.scenes['Scene'].lr_cam_bake
# Is assigned by pointer property below in class registration.
class lr_cam_bake_settings(bpy.types.PropertyGroup):
    resolution_x: bpy.props.IntProperty(name="  Width", description="", default=2048, min = 4, soft_max = 8192)
    resolution_y: bpy.props.IntProperty(name="  Height", description="", default=2048, min = 4, soft_max = 8192)
    render_device:bpy.props.EnumProperty(name= 'Device', description= '', items= [('OP1', 'CPU',''),('OP2', 'GPU','')])
    render_ao_denoise: bpy.props.BoolProperty(name="Use denoise on AO render", default=True)
    render_ao_denoise_samples: bpy.props.IntProperty(name="AO Scene Render Samples", description="", default=50, min = 1, soft_max = 200)
    export_path:bpy.props.StringProperty(name="Export Path", description="// = .blend file location\n//..\ = .blend file parent folder", default="//BakeOutput/", maxlen=1024,subtype='DIR_PATH')
    img_name:bpy.props.StringProperty(name="Name", description="Name of the rendered out image", default="BOutput")    
    img_height_suffix:bpy.props.StringProperty(name="Suffix", description="", default="_H")
    
    bdrop_color_height: bpy.props.FloatVectorProperty(
        name="Bdrop Color",
        subtype='COLOR',
        size=4,  # RGB values
        default=(0.0, 0.0, 0.0, 1.0),  # Default white color
        min=0.0,
        max=1.0
    )


#UI -------------------------------------------------------------------------------------

class VIEW3D_PT_lr_cam_bake_setup(bpy.types.Panel):
    bl_label = "Settings"
    bl_idname = "OBJECT_PT_lr_bake_setup"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LR Bake'


    def draw(self, context):
        
        lr_cam_bake = context.scene.lr_cam_bake

        layout = self.layout.box()
        


        # layout.label(text="Render")

        row = layout.row(align=True)
        row.prop(lr_cam_bake, "resolution_x")
        row.prop(lr_cam_bake, "resolution_y")
        # row = layout.row(align=True)
        
        row = layout.row(align=True)
        row.prop(lr_cam_bake, 'render_device')

        row = layout.row(align=True)
        row.prop(lr_cam_bake, 'render_ao_denoise_samples')
        row.prop(lr_cam_bake, 'render_ao_denoise')
        
       
        row = layout.row(align=True)
        row.prop(lr_cam_bake, 'img_name')
        row = layout.row(align=True)
        row.prop(lr_cam_bake, 'export_path')
        #EXPORT MODE TEMP DISABLED
        # row = layout.row(align=True)
        # if context.object:
        #     row.prop(context.object,'lr_export_type')
        row = layout.row(align=True)
        row.operator("object.lr_cam_bake", text="Render", icon = 'EXPORT')

class VIEW3D_PT_lr_cam_bake_height(bpy.types.Panel):
    bl_label = "Height"
    bl_idname = "OBJECT_PT_lr_bake_height"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LR Bake'


    def draw(self, context):
        lr_cam_bake = context.scene.lr_cam_bake

        layout = self.layout.box()
        row = layout.row(align=True)
        row.prop(lr_cam_bake, 'bdrop_color_height')
        row = layout.row(align=True)

        row.prop(lr_cam_bake, 'img_height_suffix')
        row = layout.row(align=True)
        row.operator("object.lr_cam_bake_height", text="Render Height", icon = 'EXPORT')


class VIEW3D_PT_lr_cam_bake_albedo(bpy.types.Panel):
    bl_label = "Albedo"
    bl_idname = "OBJECT_PT_lr_bake_albedo"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LR Bake'


    def draw(self, context):
        lr_cam_bake = context.scene.lr_cam_bake

        layout = self.layout.box()
        row = layout.row(align=True)

        row.operator("object.lr_cam_bake_albedo", text="Render Albedo", icon = 'EXPORT')

classes = (lr_cam_bake_settings,
            VIEW3D_PT_lr_cam_bake_setup,
            VIEW3D_PT_lr_cam_bake_albedo,
            OBJECT_OT_lr_cam_bake_albedo,
            VIEW3D_PT_lr_cam_bake_height,
            OBJECT_OT_lr_cam_bake_height,
            OBJECT_OT_lr_cam_bake)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        bpy.types.Scene.lr_cam_bake = bpy.props.PointerProperty(type=lr_cam_bake_settings)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.lr_cam_bake
