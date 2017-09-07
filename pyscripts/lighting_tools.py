import bpy
import os

bl_info = {
	"name":        "Lighting Toolbox",
	"description": "Convienient tools for lighting artists",
	"author":      "Justin Goran",
	"version":     (1, 4, 1),
	"blender":     (2, 7, 8),
	"wiki_url": "https://tangentanimation.sharepoint.com/wiki/Pages/Lighting%20Toolbox.aspx",
    "tracker_url": "",
	"location":    "View 3D > Tool Shelf",
	"category":    "3D View"
	}

#################################
#### Misc Lighting Operators ####
#################################
class ChangeExposure(bpy.types.Operator):
    '''
    Exposure control for selected light
    '''
    bl_idname = 'change.exp'
    bl_label = 'Exposure'
    exp = bpy.props.BoolProperty()
    
    def execute(self, context):
        obj = context.active_object
        light = obj.data
        
        # Create a list of nodes for selected light
        nodes = [x.name for x in light.light_data.light_nodes]
        
        # If the light has a light falloff node, adjust strength on the light falloff node, otherwise use 
        # strength on emission node
        if 'falloff' in nodes:
        
            strength = light.node_tree.nodes[light.light_data.light_nodes['falloff'].node1].inputs['Strength'].default_value
        
            # if exp value is set to true, move the exposure a stop up, otherwise move it a stop down
            if self.exp:
                light.node_tree.nodes[light.light_data.light_nodes['falloff'].node1].inputs['Strength'].default_value = float(strength*2)
            else:
                light.node_tree.nodes[light.light_data.light_nodes['falloff'].node1].inputs['Strength'].default_value = float(strength/2)
        
        else:
            strength = light.node_tree.nodes['Emission'].inputs['Strength'].default_value
            
            if self.exp:
                light.node_tree.nodes['Emission'].inputs['Strength'].default_value = float(strength*2)
            else:
                light.node_tree.nodes['Emission'].inputs['Strength'].default_value = float(strength/2)
            
        return {'FINISHED'}

class EnableNodes(bpy.types.Operator):
    bl_idname = 'enable.nodes'
    bl_label = 'Enable Nodes'
    
    def execute(self, context):
            
        obj = context.active_object
        
        obj.data.use_nodes = True
        
        return {'FINISHED'}
    
class RemoveFalloff(bpy.types.Operator):
    bl_idname = 'falloff.remove'
    bl_label = 'Remove Falloff'
    
    def execute(self, context):
        light = context.active_object.data
        
        falloff_name = light.light_data.light_nodes['falloff'].node1
        falloff_node = light.node_tree.nodes[falloff_name]
        light.node_tree.nodes.remove(falloff_node)
        
        for i in range(len(light.light_data.light_nodes)):
            if light.light_data.light_nodes[i].name == 'falloff':
                light.light_data.light_nodes.remove(i)
                break
        
        return {'FINISHED'}
              
    
##################################################################################
#### Falloff Operator for creating, changing and removing light Falloff nodes ####
##################################################################################

def update_falloff(self, context):
   
    obj = context.active_object
    light = obj.data
    
    # Light strength input
    light_strength = light.node_tree.nodes['Emission'].inputs['Strength']
    
    # Save the current light strength
    light_value = light_strength.default_value

    nodes = [x.name for x in self.light_nodes]
    
    # Check for light falloff node
    if 'falloff' in nodes:
    
        falloff_node = light.node_tree.nodes[self.light_nodes['falloff'].node1]
        
        falloff_strength = falloff_node.inputs['Strength'].default_value
        
        # None
        if light.light_data['falloff'] == 0:
            light.node_tree.nodes.remove(falloff_node)

            light_strength.default_value = float(falloff_strength)
            for i in range(len(self.light_nodes)):
                if self.light_nodes[i].name == 'falloff':
                    self.light_nodes.remove(i)
                    break
            
        # Quadratic
        elif light.light_data['falloff'] == 1:
            light.node_tree.links.new(falloff_node.outputs[0], light_strength)
            
        # Linear
        elif light.light_data['falloff'] == 2:
            light.node_tree.links.new(falloff_node.outputs[1], light_strength)
            
        # Constant
        elif light.light_data['falloff'] == 3:
            light.node_tree.links.new(falloff_node.outputs[2], light_strength) 
            
    else:
        
        if light.light_data['falloff'] != 0:
            
            falloff_node = light.node_tree.nodes.new(type="ShaderNodeLightFalloff")
            
            falloff_node.inputs['Strength'].default_value = float(light_value)
            
            if light.light_data['falloff'] == 1:
                light.node_tree.links.new(falloff_node.outputs[0], light_strength)
                
            elif light.light_data['falloff'] == 2:
                light.node_tree.links.new(falloff_node.outputs[1], light_strength)
                
            elif light.light_data['falloff'] == 3:
                light.node_tree.links.new(falloff_node.outputs[2], light_strength)
                
            new_node = obj.data.light_data.light_nodes.add()
            new_node.name = 'falloff'
            new_node.node1 = falloff_node.name
            new_node.node2 = 'Emission'                      

########################################################################
#### Gobo Operators for creating and deleting Gobo nodes for lights ####
######################################################################## 
def generate_gobo_thumbs():
    
    gobo_images = preview_collections["gobo_previews"]
    prev_location = gobo_images.images_location
    VALID_EXTENSIONS = ('.png', '.jpg', '.jpeg')

    enum_items = []

    # Generate the thumbnails
    for i, image in enumerate(os.listdir(prev_location)):
        
        if image.endswith(VALID_EXTENSIONS):
            
            
            previewpath = os.path.join(prev_location, image)
            
            gobopath = os.path.split(prev_location)
            goboimage = image.split('_preview')
            
            gobo = os.path.join(gobopath[0], '{}.png'.format(goboimage[0]))

            thumb = gobo_images.load(previewpath, previewpath, 'IMAGE')
            
            enum_items.append((gobo, goboimage[0], "", thumb.icon_id, i))

    return enum_items

def set_gobo(self, context):
    
    obj = context.active_object.data
    
    gobo_name = obj.light_data.light_nodes['gobo'].node1
    gobo_node = obj.node_tree.nodes[gobo_name]

    print(self.gobo_thumbs.split('\\'))
    gobo_node.node_tree.nodes['Image Texture'].image = bpy.data.images.load(self.gobo_thumbs)
    

class CreateGobo(bpy.types.Operator):
    bl_idname = 'gobo.create'
    bl_label = 'Create Gobo'
    
    def execute(self, context):
        obj = context.active_object
        
        # Get the node tree from the selected light
        nodetree = obj.data.node_tree
        
        # Create a new mix node and connect it to the lamp output
        mix_node = nodetree.nodes.new("ShaderNodeMixShader")      
        nodetree.links.new(mix_node.outputs[0], nodetree.nodes['Lamp Output'].inputs[0])
        nodetree.links.new(nodetree.nodes['Emission'].outputs[0], mix_node.inputs[2])
        
        # If the gobo node group already exists in the scene, create it, otherwise import it first
        if 'Gobo' in bpy.data.node_groups:
            
            gobo_node = nodetree.nodes.new("ShaderNodeGroup")
            
            gobo_orig = bpy.data.node_groups['Gobo and Projection'].copy()
            
            gobo_node.node_tree = bpy.data.node_groups[gobo_orig.name]
            
        else:
                   
            with bpy.data.libraries.load('T:\\Projects\\0053_7723\\asset\\library\\lighting\\node_groups\\Lighting Tools\\Gobo and Projection.blend', link=False) as (data_from, data_to):
                data_to.node_groups = [node for node in data_from.node_groups if node == 'Gobo and Projection']
                
            gobo_node = nodetree.nodes.new("ShaderNodeGroup")
               
            gobo_node.node_tree = bpy.data.node_groups['Gobo and Projection']
        
        if gobo.node_tree.nodes['Invert'].mute:
			gobo.node_tree.nodes['Invert'].mute = False
			
        gobo_node.node_tree.nodes['Invert'].inputs[0].default_value = 0    
        nodetree.links.new(gobo_node.outputs[0], mix_node.inputs[0])
        
        new_node = obj.data.light_data.light_nodes.add()
        new_node.name = 'gobo'
        new_node.mixer = mix_node.name
        new_node.node1 = gobo_node.name
        new_node.node2 = 'Emission'
        
        return {'FINISHED'}
    
class DeleteGobo(bpy.types.Operator):
    bl_idname = 'gobo.remove'
    bl_label = 'Remove Gobo'
    
    def execute(self, context):

        obj = context.active_object
        
        # Get the node tree from the selected light
        nodetree = obj.data.node_tree
        
        gobo = obj.data.light_data.light_nodes['gobo']
        nodetree.nodes.remove(nodetree.nodes[gobo.mixer])
        nodetree.nodes.remove(nodetree.nodes[gobo.node1])
        nodetree.links.new(nodetree.nodes['Emission'].outputs[0],nodetree.nodes['Lamp Output'].inputs[0])
        
        for i in range(len(obj.data.light_data.light_nodes)):
            if obj.data.light_data.light_nodes[i].name == 'gobo':
                obj.data.light_data.light_nodes.remove(i)
                break
                
        return {'FINISHED'}

##############################################################################
#### Projection Operators for creating and deleting Gobo nodes for lights ####
############################################################################## 
            
class CreateProjection(bpy.types.Operator):
    bl_idname = 'projection.create'
    bl_label = 'Create Projection'
    
    def execute(self, context):
        obj = context.active_object
        
        # Get the node tree from the selected light
        nodetree = obj.data.node_tree
        
        nodes = [x.name for x in obj.data.light_data.light_nodes]
            
        # If the gobo node group already exists in the scene, create it, otherwise import it first
        if 'Gobo and Projection' in bpy.data.node_groups:
            
            projection_node = nodetree.nodes.new("ShaderNodeGroup")
            
            projection_orig = bpy.data.node_groups['Gobo and Projection'].copy()
            
            projection_node.node_tree = bpy.data.node_groups[projection_orig.name]
            
        else:
                   
            with bpy.data.libraries.load('T:\\Projects\\0053_7723\\asset\\library\\lighting\\node_groups\\\\Lighting Tools\\Gobo and Projection.blend', link=False) as (data_from, data_to):
                data_to.node_groups = [node for node in data_from.node_groups if node == 'Gobo and Projection']
                
            projection_node = nodetree.nodes.new("ShaderNodeGroup")
               
            projection_node.node_tree = bpy.data.node_groups['Gobo and Projection']
            
        projection_node.node_tree.nodes['Invert'].mute = True
        new_node = obj.data.light_data.light_nodes.add()
        new_node.name = 'projection'

        new_node.node1 = projection_node.name

        if 'tmi' in nodes:
            tmi_color = nodetree.nodes[obj.data.light_data.light_nodes['tmi'].node1].inputs['Image']
            nodetree.links.new(projection_node.outputs[0], tmi_color)
            new_node.node2 = obj.data.light_data.light_nodes['tmi'].node1
            obj.data.light_data.light_nodes['tmi'].node3 = projection_node.name
            
        elif 'ies' in nodes:
            ies_color = nodetree.nodes[obj.data.light_data.light_nodes['ies'].node1].inputs['Color']
            nodetree.links.new(projection_node.outputs[0], ies_color)
            new_node.node2 = obj.data.light_data.light_nodes['ies'].node1
            obj.data.light_data.light_nodes['ies'].node3 = projection_node.name
            
        else:
            nodetree.links.new(projection_node.outputs[0], nodetree.nodes['Emission'].inputs['Color'])
            new_node.node2 = 'Emission'
        
        return {'FINISHED'}
    
class DeleteProjection(bpy.types.Operator):
    bl_idname = 'projection.remove'
    bl_label = 'Remove Projection'
    
    def execute(self, context):

        obj = context.active_object
        
        # Get the node tree from the selected light
        nodetree = obj.data.node_tree
        
        projection = obj.data.light_data.light_nodes['projection']
        nodetree.nodes.remove(nodetree.nodes[projection.node1])
        
        nodes = [x.name for x in obj.data.light_data.light_nodes]
        
        if 'tmi' in nodes:
            obj.data.light_data.light_nodes['tmi'].node3 = ''
        
        for i in range(len(obj.data.light_data.light_nodes)):
            if obj.data.light_data.light_nodes[i].name == 'projection':
                obj.data.light_data.light_nodes.remove(i)
                break
                
        return {'FINISHED'}

########################################################################
#### Gel Operators for creating and deleting Gobo nodes for lights ####
######################################################################## 
            
class CreateTMIGrade(bpy.types.Operator):
    bl_idname = 'tmigrade.create'
    bl_label = 'Create TMI Grade'
    
    def execute(self, context):
        obj = context.active_object
        
        # Get the node tree from the selected light
        nodetree = obj.data.node_tree
        
        nodes = [x.name for x in obj.data.light_data.light_nodes]

        # If the gobo node group already exists in the scene, create it, otherwise import it first
        if 'TMI Grade' in bpy.data.node_groups:
            
            tmi_node = nodetree.nodes.new("ShaderNodeGroup")
            
            tmi_orig = bpy.data.node_groups['TMI Grade'].copy()
            
            tmi_node.node_tree = bpy.data.node_groups[tmi_orig.name]

        else:
                   
            with bpy.data.libraries.load('T:\\Projects\\0053_7723\\asset\\library\\lighting\\node_groups\\\\Lighting Tools\\TMI Grade.blend', link=False) as (data_from, data_to):
                data_to.node_groups = [node for node in data_from.node_groups if node == 'TMI Grade']
                
            tmi_node = nodetree.nodes.new("ShaderNodeGroup")
               
            tmi_node.node_tree = bpy.data.node_groups['TMI Grade']        
            
        new_node = obj.data.light_data.light_nodes.add()
        new_node.name = 'tmi'
        new_node.node1 = tmi_node.name
                    
        if 'ies' in nodes:
            ies_color = nodetree.nodes[obj.data.light_data.light_nodes['ies'].node1].inputs[2]
            
            tmi_node.inputs['Image'].default_value = ies_color.default_value
            
            nodetree.links.new(tmi_node.outputs[0], ies_color)
            
            new_node.node2 = obj.data.light_data.light_nodes['ies'].node1
            
        else:
            
            tmi_node.inputs['Image'].default_value = nodetree.nodes['Emission'].inputs[0].default_value 
            nodetree.links.new(tmi_node.outputs[0], nodetree.nodes['Emission'].inputs[0])
            new_node.node2 = 'Emission'
        
        if 'projection' in nodes:
                
            projection = nodetree.nodes[obj.data.light_data.light_nodes['projection'].node1].outputs[0]
            obj.data.light_data.light_nodes['projection'].node2 = tmi_node.name    
            nodetree.links.new(projection, tmi_node.inputs[0])
            
            new_node.node3 = obj.data.light_data.light_nodes['projection'].node1
            

        
        return {'FINISHED'}
    
class DeleteTMIGrade(bpy.types.Operator):
    bl_idname = 'tmigrade.remove'
    bl_label = 'Remove TMI Grade'
    
    def execute(self, context):

        obj = context.active_object
        
        # Get the node tree from the selected light
        nodetree = obj.data.node_tree
        
        tmi = obj.data.light_data.light_nodes['tmi']
        color = nodetree.nodes[tmi.node1].inputs['Image'].default_value
        nodetree.nodes.remove(nodetree.nodes[tmi.node1])
        
        if tmi.node3:
            projection = nodetree.nodes[tmi.node3].outputs[0]
            obj.data.light_data.light_nodes['projection'].node2 = tmi.node2
            nodetree.links.new(projection, nodetree.nodes[tmi.node2].inputs['Color'])
        else:
            nodetree.nodes[tmi.node2].inputs['Color'].default_value = color
        
        for i in range(len(obj.data.light_data.light_nodes)):
            if obj.data.light_data.light_nodes[i].name == 'tmi':
                obj.data.light_data.light_nodes.remove(i)
                break
                
        return {'FINISHED'}
            
######################################################################
#### IES Operators for creating and deleting IES nodes for lights ####
######################################################################

def generate_thumbs():
    
    ies_images = preview_collections["thumbnail_previews"]
    image_location = ies_images.images_location
    VALID_EXTENSIONS = ('.png', '.jpg', '.jpeg')

    enum_items = []

    # Generate the thumbnails
    for i, image in enumerate(os.listdir(image_location)):
        if image.endswith(VALID_EXTENSIONS):
            filepath = os.path.join(image_location, image)
            thumb = ies_images.load(filepath, filepath, 'IMAGE')
            img_num = image.split('.')
            img_num = img_num[0].split('_')
            enum_items.append((img_num[1], image, "", thumb.icon_id, i))

    return enum_items

def set_ies(self, context):
    
    obj = context.active_object.data
    
    ies_node = obj.light_data.light_nodes['ies'].node1
    
    obj.node_tree.nodes[ies_node].inputs[0].default_value = float(self.ies_thumbs)
    
class CreateIES(bpy.types.Operator):
    bl_idname = 'ies.create'
    bl_label = 'Create IES'
    
    def execute(self, context):
        obj = context.active_object
        
        # Get the node tree from the selected light
        nodetree = obj.data.node_tree
        if obj.data.type == 'SPOT':
            obj.data.spot_size = 3.141593
        
        nodes = [x.name for x in obj.data.light_data.light_nodes]
        
        # If the gobo node group already exists in the scene, create it, otherwise import it first        
        if 'IES Shader' in bpy.data.node_groups:
            
            ies_node = nodetree.nodes.new("ShaderNodeGroup")
            ies_copy = bpy.data.node_groups['IES Shader'].copy()
            ies_node.node_tree = bpy.data.node_groups[ies_copy.name] 
  
        else:
            with bpy.data.libraries.load('T:\\Projects\\0053_7723\\asset\\library\\lighting\\node_groups\\Lighting Tools\\IES Shader.blend', link=False) as (data_from, data_to):
                data_to.node_groups = [node for node in data_from.node_groups if node == 'IES Shader']
                      
            ies_node = nodetree.nodes.new("ShaderNodeGroup")
            ies_node.node_tree = bpy.data.node_groups['IES Shader']
        
        ies_node.inputs['Color'].default_value = nodetree.nodes['Emission'].inputs['Color'].default_value
        nodetree.links.new(ies_node.outputs[0], nodetree.nodes['Emission'].inputs['Color'])
        if 'tmi' in nodes:
            nodetree.links.new(nodetree.nodes[obj.data.light_data.light_nodes['tmi'].node1].outputs[0], ies_node.inputs[2])
            obj.data.light_data.light_nodes['tmi'].node2 = ies_node.name
            
        elif 'projection' in nodes:    
            nodetree.links.new(nodetree.nodes[obj.data.light_data.light_nodes['projection'].node1].outputs[0], ies_node.inputs[2])
            obj.data.light_data.light_nodes['projection'].node2 = ies_node.name
        
        new_node = obj.data.light_data.light_nodes.add()
        new_node.name = 'ies'
        new_node.node1 = ies_node.name
        new_node.node2 = 'Emission'
        
        return {'FINISHED'}
    
class DeleteIES(bpy.types.Operator):
    bl_idname = 'ies.remove'
    bl_label = 'Remove IES'
    
    def execute(self, context):

        obj = context.active_object
        
        # Get the node tree from the selected light
        nodetree = obj.data.node_tree
        
        nodes = [x.name for x in obj.data.light_data.light_nodes]
        
        ies = obj.data.light_data.light_nodes['ies']
        color = nodetree.nodes[ies.node1].inputs['Color'].default_value
        nodetree.nodes.remove(nodetree.nodes[ies.node1])
        
        if 'tmi' in nodes:
            nodetree.links.new(nodetree.nodes[obj.data.light_data.light_nodes['tmi'].node1].outputs[0], nodetree.nodes['Emission'].inputs[0])
            obj.data.light_data.light_nodes['tmi'].node2 = 'Emission'
            
        elif 'projection' in nodes:
            nodetree.links.new(nodetree.nodes[obj.data.light_data.light_nodes['projection'].node1].outputs[0], nodetree.nodes['Emission'].inputs[0])
            obj.data.light_data.light_nodes['projection'].node2 = 'Emission'
        else:
            nodetree.nodes['Emission'].inputs[0].default_value = color
        
        for i in range(len(obj.data.light_data.light_nodes)):
            if obj.data.light_data.light_nodes[i].name == 'ies':
                obj.data.light_data.light_nodes.remove(i)
                break
                
        return {'FINISHED'}
    
#########################
#### Property Groups ####
#########################
def invert_gobo(self, context):
    
    light = context.active_object.data
    
    gobo = light.node_tree.nodes[light.light_data.light_nodes[self.name].node1]
    
    invert = gobo.node_tree.nodes['Invert'].inputs[0]
    
    invert.default_value = self.invert

preview_collections = {}

class IESLibrary(bpy.types.PropertyGroup):
    
    ies_images = bpy.utils.previews.new()
    ies_images.images_location = 'T:\\Projects\\0053_7723\\asset\\library\\lighting\\ies_preview'    
    preview_collections["thumbnail_previews"] = ies_images

class GoboLibrary(bpy.types.PropertyGroup):
    
    gobo_images = bpy.utils.previews.new()
    gobo_images.images_location = 'T:\\Projects\\0053_7723\\asset\\library\\lighting\\gobos\\preview'    
    preview_collections["gobo_previews"] = gobo_images

class NodeCollection(bpy.types.PropertyGroup):
    
    mixer = bpy.props.StringProperty()
    node1 = bpy.props.StringProperty()
    node2 = bpy.props.StringProperty()
    node3 = bpy.props.StringProperty()
    invert = bpy.props.BoolProperty(update=invert_gobo, default=False)  

class LightSettings(bpy.types.PropertyGroup):
    
    falloff_options = [('light.none', "None", '', '', 0),
                        ('light.quadratic', "Quadratic", '', '', 1),
                        ('light.linear', 'Linear', '', '', 2),
                        ('light.constant', 'Constant', '', '', 3)]
    
    falloff = bpy.props.EnumProperty(items=falloff_options, name='Falloff', update=update_falloff)
    
    light_nodes = bpy.props.CollectionProperty(type=NodeCollection)
    
    ies_thumbs = bpy.props.EnumProperty(items=generate_thumbs(), update=set_ies)
    
    gobo_thumbs = bpy.props.EnumProperty(items=generate_gobo_thumbs(), update=set_gobo)
    
    custom_gobo = bpy.props.BoolProperty(default=False)

##############################
#### Lighting Toolbox GUI ####
##############################

class LightProperties(bpy.types.Panel):
    bl_category = 'Lighting Toolbox'
    bl_label = 'Light Toolbox'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    
    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and context.active_object.type == 'LAMP')
    
    def draw(self, context):
    
        layout = self.layout
        light = context.active_object.data
        clight = light.cycles
  
        ### Make sure 'Use Nodes' is enabled on the selected light ###
        
        if not light.use_nodes or light.type == 'HEMI':
                                        
            if light.type == 'HEMI':
                ### Light type changer ###
                layout.prop(light, 'type', expand=True)
                layout.label(text="Not supported, please change light type")
            else:
                layout.label("Warning: 'Use Nodes' is not enabled for this light")
                layout.operator('enable.nodes')
        
        else:
            
            ### Light type changer ###
            layout.prop(light, 'type', expand=True)
            
            ### Light shape and shadow settings ###
            sampling = False
            
            if context.scene.cycles.progressive == 'BRANCHED_PATH':
                if context.scene.cycles.sample_all_lights_direct or context.scene.cycles.sample_all_lights_indirect:
                    sampling = True
            
            top_box = layout.box()
            
            split = top_box.split()
            col = split.column(align=True)
            
            if light.type in {'POINT', 'SUN', 'SPOT'}:
                col.prop(light, "shadow_soft_size", text="Size")            
                sub = col.column(align=True)
            
            if light.type == 'AREA':
                
                col.prop(light, "shape", text="")
                sub = col.column(align=True)
                    
                if light.shape == 'SQUARE':
                    sub.prop(light, "size")
                    
                elif light.shape == 'RECTANGLE':
                    sub.prop(light, "size", text="Size X")
                    sub.prop(light, "size_y", text="Size Y")
            
            col = split.column(align=True)
            
            if sampling:
                sub.prop(clight, "samples")
            if not clight.is_portal:
                sub.prop(clight, "max_bounces")                
                col.prop(clight, "cast_shadow")
                col.prop(clight, "use_multiple_importance_sampling", text="Multiple Importance")
                
            if light.type == 'AREA':
                 col.prop(clight, "is_portal", text="Portal") 

            nodes = [x.name for x in light.light_data.light_nodes]
            
            ### Light Color/Strength/Falloff Properties ###
            
            if not clight.is_portal or light.type != 'AREA' and clight.is_portal:
                
                layout.label('Light Properties')
                prop_box = layout.box()

                prop_box.label('Intensity')
                
                mainrow = prop_box.row(align=True)      
                mainrow_split = mainrow.split(percentage=0.6,align=True)
                
                if 'falloff' in nodes and light.type != 'SUN':
                    mainrow_split.prop(light.node_tree.nodes[light.light_data.light_nodes['falloff'].node1].inputs['Strength'], 'default_value', 'Strength')
                    prop_box.prop(light.node_tree.nodes[light.light_data.light_nodes['falloff'].node1].inputs['Smooth'], 'default_value', 'Smooth')
                else:
                    mainrow_split.prop(light.node_tree.nodes['Emission'].inputs['Strength'], 'default_value', 'Strength')

                mainrow_split.operator('change.exp', text='-1 Stop').exp = False   
                mainrow_split.operator('change.exp', text='+1 Stop').exp = True
                
                if light.type != 'SUN':
                    prop_box.label('Falloff')
                    row = prop_box.row()
                    row.prop(light.light_data, 'falloff', expand=True)

                elif 'falloff' in nodes:
                    prop_box.label('Falloff')
                    prop_box.label('Sun lamp does not support falloff node, please remove')
                    prop_box.operator('falloff.remove')
                         
                if 'tmi' in nodes:
                    tmi = light.light_data.light_nodes['tmi']
                    
                    if 'projection' not in nodes:
                        prop_box.prop(light.node_tree.nodes[tmi.node1].inputs['Image'], 'default_value', 'Color')
                        
                    prop_box.prop(light.node_tree.nodes[tmi.node1].inputs[1], 'default_value', 'Warmer/Colder')
                    prop_box.prop(light.node_tree.nodes[tmi.node1].inputs[2], 'default_value', 'Green/Magenta')
                    prop_box.prop(light.node_tree.nodes[tmi.node1].inputs[3], 'default_value', 'Intensity')
                    
                elif 'ies' in nodes:
                    ies = light.light_data.light_nodes['ies']
                    prop_box.prop(light.node_tree.nodes[ies.node1].inputs['Color'], 'default_value', 'Color')        
                                        
                elif 'projection' not in nodes:
                    prop_box.prop(light.node_tree.nodes['Emission'].inputs[0], 'default_value', 'Color')
                
                ### Spotlight Cone Controls ###
            
                if light.type == 'SPOT' and 'ies' not in nodes:
                    
                    layout.label('Spot Controls')
                    box = layout.box()
                    split = box.split()

                    col = split.column()
                    sub = col.column()
                    sub.prop(light, "spot_size", text="Size")
                    sub.prop(light, "spot_blend", text="Blend", slider=True)

                    col = split.column()
                    col.prop(light, "show_cone")
                    
                ### Light Extras ###
                    
                layout.label('Light Extras')
                extra_box = layout.box()
                
                if 'tmi' in nodes:
                    extra_box.operator('tmigrade.remove')
                else:
                    extra_box.operator('tmigrade.create')
                    
                if light.type == 'SUN':
                    extra_box.label('Sun lamp does not support Gobos, Projections, or IES')
                    extra_box.label('please remove any extras if they exist')
                
                if 'gobo' in nodes:
                    extra_box.operator('gobo.remove')
                    
                elif light.type not in {'AREA', 'SUN'}:
                    extra_box.operator('gobo.create')

                if 'projection' in nodes:
                    extra_box.operator('projection.remove')                    
                elif light.type != 'SUN':
                    extra_box.operator('projection.create')
    
                if 'ies' in nodes:
                    extra_box.operator('ies.remove')
                                    
                elif light.type not in {'AREA', 'POINT', 'SUN'}:
                    extra_box.operator('ies.create')
            
class GoboPanel(bpy.types.Panel):
    bl_category = 'Lighting Toolbox'
    bl_label = 'Gobo Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    
    @classmethod
    def poll(cls, context):
        if context.active_object is not None:
            if context.active_object.type == 'LAMP':
                nodes = [node.name for node in context.active_object.data.light_data.light_nodes]
                if 'gobo' in nodes:
                    return True
        else:
            return False
        
    def draw(self, context):
    
        layout = self.layout
        light = context.active_object.data

        gobo = light.light_data.light_nodes['gobo']
        
        gobo_node = light.node_tree.nodes[gobo.node1]
        gobo_ntree = gobo_node.node_tree
        gobo_image = gobo_node.node_tree.nodes['Image Texture']
        
        layout.prop(gobo_node.inputs['Scale X'], 'default_value', 'Scale X')
        layout.prop(gobo_node.inputs['Scale Y'], 'default_value', 'Scale Y')
        layout.prop(gobo_node.inputs['Rotation'], 'default_value', 'Rotation')
        layout.prop(gobo, 'invert')
        
        layout.prop(light.light_data, "custom_gobo", "Use Custom Gobo")
        
        if light.light_data.custom_gobo:
            layout.template_node_view(gobo_ntree, gobo_image, None)
        else:
            layout.label('Gobo Library')
            layout.template_icon_view(light.light_data, 'gobo_thumbs',scale=10, show_labels=True)

class IESPanel(bpy.types.Panel):
    bl_category = 'Lighting Toolbox'
    bl_label = 'IES Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    
    @classmethod
    def poll(cls, context):
        if context.active_object is not None:
            obj = context.active_object
            if obj.type == 'LAMP':
                nodes = [node.name for node in obj.data.light_data.light_nodes]
                if 'ies' in nodes:
                    return True
        else:
            return False
        
    def draw(self, context):
    
        layout = self.layout
        light = context.active_object.data

        ies = light.light_data.light_nodes['ies']
        
        layout.label('IES Settings')
        
        ies_box = layout.box()
                                
        ies_box.prop(light.node_tree.nodes[light.light_data.light_nodes['ies'].node1].inputs['Scale'], 'default_value', 'Scale')
        
        ies_box.template_icon_view(light.light_data, 'ies_thumbs', scale=5, show_labels=True)
        
class ProjectionPanel(bpy.types.Panel):
    bl_category = 'Lighting Toolbox'
    bl_label = 'Projection Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    
    @classmethod
    def poll(cls, context):
        if context.active_object is not None:
            obj = context.active_object
            if obj.type == 'LAMP':
                nodes = [node.name for node in obj.data.light_data.light_nodes]
                if 'projection' in nodes:
                    return True
        else:
            return False
        
    def draw(self, context):
    
        layout = self.layout
        light = context.active_object.data

        projection = light.light_data.light_nodes['projection']
        
        projection_node = light.node_tree.nodes[projection.node1]
        projection_ntree = projection_node.node_tree
        projection_image = projection_node.node_tree.nodes['Image Texture']

        layout.prop(projection_node.inputs['Scale X'], 'default_value', 'Scale X')
        layout.prop(projection_node.inputs['Scale Y'], 'default_value', 'Scale Y')
        layout.prop(projection_node.inputs['Rotation'], 'default_value', 'Rotation')
        layout.template_node_view(projection_ntree, projection_image, None)
           
# Registration
def register():
    bpy.utils.register_module(__name__)
    bpy.types.Lamp.light_data = bpy.props.PointerProperty(type=LightSettings)
    bpy.types.Scene.ies_lib = bpy.props.PointerProperty(type=IESLibrary)


def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Lamp.light_data
    del bpy.types.Scene.ies_lib

if __name__ == "__main__":
    register()