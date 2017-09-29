import bpy, os
from shutil import copyfile, copy

bl_info = {
	"name":        "Node Group Manager",
	"description": "Convienient tools for appending, linking, and saving node groups",
	"author":      "Justin Goran",
	"version":     (1, 0, 0),
	"blender":     (2, 7, 8),
	"wiki_url": "",
    "tracker_url": "",
	"location":    "Node Editor > Tool Shelf",
	"category":    "Node"
	}

##############################
#### Master Path Settings ####
##############################
base_path = 'T:\\Projects\\0053_7723\\asset\\library\\lighting\\node_groups'
empty_blend = 'T:\\Projects\\0053_7723\\asset\\library\\lighting\\node_groups\\empty.blend'
user = os.getlogin()

###################
#### Functions ####
###################

def update_node_lst(self, context):
	
	# Clear the node list to repopulate it
    self.node_lst.clear()
    
    selected = self.cat_lst
    cat_path = os.path.join(base_path, selected)
    
    files = os.listdir(cat_path)
    
    for file in files:
        if os.path.isfile(os.path.join(cat_path, file)):
            
            if os.path.splitext(file)[1] == '.blend':
                node = self.node_lst.add()
                node.name = os.path.splitext(file)[0]
                
                if os.path.isfile(os.path.join(cat_path, '{}_desc.txt'.format(node.name))):
                    with open(os.path.join(cat_path, '{}_desc.txt'.format(node.name)), 'r') as txtfile:
                        node.desc = txtfile.readlines()[0]


def update_cat_lst(self, context):
    
    cat_folder = os.listdir(base_path)
    
    categories = []
    
    for cat in cat_folder:
        if os.path.isdir(os.path.join(base_path,cat)):
            categories.append((cat, cat, ''))
    
    return categories

#########################
#### Control Classes ####
#########################

class GetNodeName(bpy.types.Operator):
    bl_idname = 'nodes.name'
    bl_label = 'Get Name'
    
    def execute(self, context):
        
        bpy.context.scene.custom_nodes.ng_name = context.active_node.node_tree.name
        
        return {'FINISHED'}

class CUSTOMNODES_UL_customnodes(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
			layout.prop(item, "name", text="", emboss=False)
			layout.prop(item, "desc", text="", emboss=False)
			
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label("")
            
class ExportNodes(bpy.types.Operator):
    
    bl_idname = 'nodes.save'
    bl_label = 'Save'
    
    def execute(self, context):
        
        ng_name = bpy.context.scene.custom_nodes.ng_name
        sel = context.active_node.node_tree.name
		
		node_group = bpy.data.node_groups[sel]
        
        user_path = os.path.join(base_path, user)
        
        arch_path = os.path.join(user_path, 'archive')
        
        new_file = '{}\\{}.blend'.format(user_path, ng_name)
        
        ### Check if file and folders exist ###
        
        if not os.path.exists(user_path):
            os.mkdir(user_path)
        
        if not os.path.exists(arch_path):
            os.mkdir(arch_path)
        
        if os.path.exists(new_file):
            exists = True
            version = 1
            while exists:
                arch_file = '{0}\\{1}_V{2:04d}.blend'.format(arch_path, ng_name, version)
                if os.path.exists(arch_file):
                    version +=1
                else:
                    copy(new_file, arch_file)
                    exists = False        
                
            copy(new_file, arch_path)
        
        ### Copy empty blender file and write the node_group to that file ###
        copyfile(empty_blend, new_file)
        bpy.data.libraries.write(new_file, {node_group}, fake_user=True, compress=True)
        
		with open('{}\\{}_desc.txt'.format(user_path, ng_name), 'w') as txtfile:
            txtfile.write(bpy.context.scene.custom_nodes.ng_desc)
        
        ### Update node list ###
        self = bpy.context.scene.custom_nodes
        update_node_lst(self, context)
               
        return {'FINISHED'}
    
class ImportNodes(bpy.types.Operator):
    
    bl_idname = 'nodes.append'
    bl_label = 'Append'
    create = bpy.props.BoolProperty(default=False)
    
    def execute(self, context):
        
		# Get the selected node name
        node_props = bpy.context.scene.custom_nodes
        node_name = node_props.node_lst[node_props.index].name
		
		# Get path for the node to import
        sel_cat = bpy.context.scene.custom_nodes.cat_lst        
        cat_path = os.path.join(base_path, sel_cat)
        
		# Append the selected node group 
        with bpy.data.libraries.load('{}\\{}.blend'.format(cat_path, node_name), link=False) as (data_from, data_to):
            data_to.node_groups = [node for node in data_from.node_groups if node == node_name]   
        
		# If the user clicked append and create
		if self.create:
			
			# Is this a shader node group or a compositing node group
			if bpy.data.node_groups[node_name].type == 'SHADER': 
				if context.active_object.type == 'MESH':
					nodetree = context.active_object.active_material.node_tree
				else:
					nodetree = context.active_object.data.node_tree
					
				node = nodetree.nodes.new("ShaderNodeGroup")
				node.node_tree = bpy.data.node_groups[node_name]
					
			elif bpy.data.node_groups[node_name].type == 'COMPOSITING':
			
				nodetree = bpy.context.scene.node_tree
				node = nodetree.nodes.new("CompositorNodeGroup")
				node.node_tree = bpy.data.node_groups[node_name]
				
        return {'FINISHED'}    

#########################
#### Property Groups ####
#########################

class CustomNodeGroups(bpy.types.PropertyGroup):
                
    desc = bpy.props.StringProperty() 
    
class CustomNodeProperties(bpy.types.PropertyGroup):
    
	index = bpy.props.IntProperty(default = -1, min=-1)
	
	node_lst = bpy.props.CollectionProperty(type=CustomNodeGroups)
	
	# Generate it's items from the Node Group Directory (update_cat_lst), and when the value changes
	# run update_node_lst to populate node_lst
	
    cat_lst = bpy.props.EnumProperty(name = 'Categories', items = update_cat_lst, update = update_node_lst)
    
    ### ng saver settings, ng = Node Group ###
    ng_name = bpy.props.StringProperty()
    ng_desc = bpy.props.StringProperty()
    

###############
#### Panel ####
###############
      
class NodeImporter(bpy.types.Panel):
    
    bl_category = 'Custom Nodes'
    bl_label = 'Node Group Appender'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    
    def draw(self, context):
        
        layout = self.layout
        np = bpy.context.scene.custom_nodes
        
        #### Category drop-down ####
        layout.prop(np, 'cat_lst')
        
        #### Node List ####
        layout.template_list('CUSTOMNODES_UL_customnodes', '', np, 'node_lst', np, 'index')

        #### Controls ####
        layout.operator('nodes.append')
        layout.operator('nodes.append', 'Append and Create').create = True
        
class NodeExporter(bpy.types.Panel):
    bl_category = 'Custom Nodes'
    bl_label = 'Node Group Saver'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    
    @classmethod
    def poll(self, context):
        
        try:
            if context.active_node.node_tree:
                has_nodetree = True
        except AttributeError:
            has_nodetree = False
            
        return (context.active_node is not None and has_nodetree)
        
    
    def draw(self, context):
        layout = self.layout
        np = bpy.context.scene.custom_nodes
        
        namerow = layout.row(align=True)
        namerowsplit = namerow.split(percentage=0.8, align=True)
        
        namerowsplit.prop(np, 'ng_name', 'Name')
        namerowsplit.operator('nodes.name')
        
        layout.prop(np, 'ng_desc', 'Description')
        layout.operator('nodes.save')    
            
######################
#### Registration ####
######################

def register():
    bpy.utils.register_module(__name__)   
    bpy.types.Scene.custom_nodes = bpy.props.PointerProperty(type=CustomNodeProperties)

def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.custom_nodes

if __name__ == "__main__":
    register() 