import bpy, os
from shutil import copyfile, copy

bl_info = {
    "name":        "Node Group Manager",
    "description": "Convienient tools for appending, linking, and saving node groups",
    "author":      "Justin Goran",
    "version":     (1, 1, 0),
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
                
                node.node_name = node.name
                
                if os.path.isfile(os.path.join(cat_path, '{}_desc.txt'.format(node.name))):
                    with open(os.path.join(cat_path, '{}_desc.txt'.format(node.name)), 'r') as txtfile:
                        lines = txtfile.readlines()
                        node.desc = lines[0].strip()
                        if len(lines) > 2:
                            node.type = lines[2].strip()


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
            txtfile.write(bpy.context.scene.custom_nodes.ng_desc + '\n' + sel + '\n' + node_group.type)
        
        ### Update node list ###
        self = bpy.context.scene.custom_nodes
        update_node_lst(self, context)
               
        return {'FINISHED'}
    
class ImportNodes(bpy.types.Operator):
    
    bl_idname = 'nodes.append'
    bl_label = 'Append'
    create = bpy.props.BoolProperty(default=False)
    
    def execute(self, context):
        
        # Get path for the node to import
        sel_cat = bpy.context.scene.custom_nodes.cat_lst        
        cat_path = os.path.join(base_path, sel_cat)
        
        # Get the selected node name
        node_props = bpy.context.scene.custom_nodes
        node_name = node_props.node_lst[node_props.index].name
        
        if os.path.isfile(os.path.join(cat_path, '{}_desc.txt'.format(node_name))):
            with open(os.path.join(cat_path, '{}_desc.txt'.format(node_name)), 'r') as txtfile:
                lines = txtfile.readlines()
                if len(lines) <= 1:
                    realname = node_name
                else:
                    realname = lines[1].strip()
            txtfile.close()
        else:
            realname = node_name
            
        # Append the selected node group 
        with bpy.data.libraries.load('{}\\{}.blend'.format(cat_path, node_name), link=False) as (data_from, data_to):
            data_to.node_groups = [node for node in data_from.node_groups if node == realname]   
        
        # If the user clicked append and create
        if self.create:
            
            # Is this a shader node group or a compositing node group
            if bpy.data.node_groups[realname].type == 'SHADER': 
                if context.active_object.type == 'MESH':
                    nodetree = context.active_object.active_material.node_tree
                else:
                    nodetree = context.active_object.data.node_tree
                    
                node = nodetree.nodes.new("ShaderNodeGroup")
                node.node_tree = bpy.data.node_groups[realname]
                    
            elif bpy.data.node_groups[realname].type == 'COMPOSITING':
            
                nodetree = bpy.context.scene.node_tree
                node = nodetree.nodes.new("CompositorNodeGroup")
                node.node_tree = bpy.data.node_groups[realname]
                
        return {'FINISHED'}
        
class DeleteNodes(bpy.types.Operator):
    
    bl_idname = 'nodes.del'
    bl_label = 'Delete'
    
    def execute(self, context):
    
        sel_cat = bpy.context.scene.custom_nodes.cat_lst        
        cat_path = os.path.join(base_path, sel_cat)
        
        # Get the selected node name
        node_props = bpy.context.scene.custom_nodes
        node_name = node_props.node_lst[node_props.index].name
        
        node_file = os.path.join(cat_path, '{}.blend'.format(node_name))
        node_desc = os.path.join(cat_path, '{}_desc.txt'.format(node_name))
        
        if sel_cat == user:
            if os.path.isfile(node_file):
                os.remove(node_file)
            if os.path.isfile(node_desc):
                os.remove(node_desc)
        
        ### Update node list ###
        self = bpy.context.scene.custom_nodes
        update_node_lst(self, context)
        
        return {'FINISHED'}
            
#########################
#### Property Groups ####
#########################

def rename_name(self, context):
    sel_cat = bpy.context.scene.custom_nodes.cat_lst
    if sel_cat == user:
     
        cat_path = os.path.join(base_path, sel_cat)
            
        node_file = os.path.join(cat_path, '{}.blend'.format(self.name))
        node_desc = os.path.join(cat_path, '{}_desc.txt'.format(self.name))
                    
        if self.name != self.node_name:
            if os.path.isfile(node_file):
                os.rename(node_file, os.path.join(cat_path, '{}.blend'.format(self.node_name)))
                
            if os.path.isfile(node_desc):
                with open(node_desc, 'r') as txtfile:
                    lines = txtfile.readlines()
                txtfile.close()
            
                if len(lines) == 1:
                    lines[0] = '{}\n'.format(lines[0])
                    lines.append(self.name)
            
                    with open(node_desc, 'w') as txtfile:
                        txtfile.writelines(lines)
                    txtfile.close()
                    
                os.rename(node_desc, os.path.join(cat_path, '{}_desc.txt'.format(self.node_name)))
            else:
                with open(os.path.join(cat_path, '{}_desc.txt'.format(self.node_name)), 'w') as descfile:
                    lines = ['\n', self.name]
                    descfile.writelines(lines)
                descfile.close()
                    
            self.name = self.node_name
        
def rename_desc(self, context):

    sel_cat = bpy.context.scene.custom_nodes.cat_lst
    if sel_cat == user:        
        cat_path = os.path.join(base_path, sel_cat)
        node_desc = os.path.join(cat_path, '{}_desc.txt'.format(self.name))
        
        if os.path.isfile(node_desc):
            
            with open(node_desc, 'r') as txtfile:
                lines = txtfile.readlines()
            txtfile.close()
                
            if lines[0].strip() != self.desc.strip():
                lines[0] = self.desc + '\n'

                with open(node_desc, 'w') as txtfile:
                    txtfile.writelines(lines)
                txtfile.close()
        else:
            with open(node_desc, 'w') as txtfile:
                lines = [self.desc + '\n', self.name]
                txtfile.writelines(lines)
            txtfile.close()
    
class CUSTOMNODES_UL_customnodes(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
    
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            firstclmn = layout.split(0.3, align=True)

            firstclmn.prop(item, "node_name", text="", emboss=False)

            desc_clmn = firstclmn.split(0.3, align=True)

            desc_clmn.prop(item, "type", text="", emboss=False)
            
            desc_clmn.prop(item, "desc", text="", emboss=False)
            
        elif self.layout_type == 'GRID':
            layout.alignment = 'LEFT'
            layout.label("")
            
class CustomNodeGroups(bpy.types.PropertyGroup):
    
    node_name = bpy.props.StringProperty(update=rename_name)
    desc = bpy.props.StringProperty(update=rename_desc)
    type = bpy.props.StringProperty()
    
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
        layout.operator('nodes.append').create = False
        layout.operator('nodes.append', 'Append and Create').create = True
        if np.cat_lst == user:
            layout.operator('nodes.del')
        
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