"""
analyzing Python code files in a given directory, extracting information about functions,
classes, imports, and more, and storing this information in structured JSON files for further analysis and
documentation.
The input variables required are the PACKAGE_DIRECTORY,PACKAGE_NAME, and REPO_AUTHOR environment variables --> Provided
by parse_github_repos.py
and the output includes JSON files for the repository, containing each of these datapoints:.
'id', 'filePath', 'numLines', 'lineStart', 'lineEnd', 'numParams', 'signature',
'comment', 'numCommentLines', 'content', 'parentClass', 'packageName', 'imports'
"""

import ast
import astor
import os
import pandas as pd
import json
import hashlib

directory = os.environ['PACKAGE_DIRECTORY']
package_name = os.environ['PACKAGE_NAME']
author = os.environ['REPO_AUTHOR']

skip_dirs = ['tests', 'testsystems', '__pycache__', 'exampledata', 'example', 'docs', 'test', 'examples', 'cython']
skip_files = ['__init__.py', '_version.py', 'utils_for_testing.py', 'GUI.py', 'citation.py', 'version.py', 'basedir.py', 'setup.py']
skip_assign = ['__authors__', '__license__', 'LongWarning', '__credits', '__credits__', '__email__', 'SCOARY_VERSION', '__author__', '__copyright__']
skip_functions = ['main']

global df
df = pd.DataFrame(columns=['id', 'filePath', 'numLines', 'lineStart', 'lineEnd', 'numParams', 'signature', 'comment', 'numCommentLines', 'content', 'parentClass', 'packageName', 'imports'])

global file_imports
file_imports = {}

file_list = []

def add_files(cur_dir):
    for file in os.listdir(cur_dir):
        f = os.path.join(cur_dir, file)

        if os.path.isfile(f):
            if not file.endswith('.py'):
                continue

            should_continue = False

            for file_name in skip_files:
                if file == file_name:
                    should_continue = True
                    break
            
            if should_continue:
                continue
            
            file_list.append(f)
        elif os.path.isdir(f):
            should_continue = False

            for dir in skip_dirs:
                if file == dir:
                    should_continue = True
                    break
            
            if should_continue:
                continue

            add_files(f)

add_files(directory)

def turn_package_to_file(package):
    package = package.split('.')
    file = ''
    for i in range(1, len(package) - 1):
        file += package[i] + '/'
    file += package[len(package) - 1] + '.py'
    file = os.path.join(directory, file)
    return file

for f in file_list:
    if os.path.isfile(f):
        r = open(f, 'r')
        try:
            t = ast.parse(r.read())
        except:
            continue

        global custom_imports, global_variables, import_statements, function_declarations, class_declarations

        custom_imports = []
        global_variables = []
        import_statements = []
        function_declarations = []
        class_declarations = []

        module_name = package_name
        for item in f[(len(directory) + 1):].split('/'):
            module_name += '.' + item
        module_name = module_name[:-3]

        for node in t.body:
            match node.__class__.__name__:
                case 'Import':
                    for name in node.names:
                        if name.name.split('.')[0] == package_name:
                            if name.name not in custom_imports and turn_package_to_file(name.name) in file_list:
                                custom_imports.append(name.name)
                        else:
                            if name.name[0] == '.':
                                if len(name.name) > 1 and name.name[1] == '.':
                                    new_import = module_name[:module_name[:module_name.rfind('.')].rfind('.')] + name.name[1:]
                                    if new_import not in custom_imports and turn_package_to_file(new_import) in file_list:
                                        custom_imports.append(new_import)
                                else:
                                    new_import = module_name[:module_name.rfind('.')] + name.name
                                    if new_import not in custom_imports and turn_package_to_file(new_import) in file_list:
                                        custom_imports.append(new_import)
                    import_statements.append(astor.to_source(node))
                case 'ImportFrom':
                    if node.module == None:
                        for name in node.names:
                            new_import = module_name[:module_name.rfind('.')] + '.' + name.name
                            if new_import not in custom_imports and turn_package_to_file(new_import) in file_list:
                                custom_imports.append(new_import)
                            new_import = module_name[:module_name[:module_name.rfind('.')].rfind('.')] + '.' + name.name
                            if new_import not in custom_imports and turn_package_to_file(new_import) in file_list:
                                custom_imports.append(new_import)
                    elif node.module.split('.')[0] == package_name:
                        for name in node.names:
                            new_import = node.module + '.' + name.name
                            if new_import not in custom_imports and turn_package_to_file(new_import) in file_list:
                                custom_imports.append(new_import)
                    import_statements.append(astor.to_source(node))
                case 'Assign':
                    node_check = node.targets[0]

                    should_continue = False

                    for var_name in skip_assign:
                        if node_check.__class__.__name__ == 'Name' and node_check.id == var_name:
                            should_continue = True
                            break
                    
                    if should_continue:
                        continue

                    global_variables.append(astor.to_source(node))
                case 'Try':
                    for try_node in node.body:
                        match try_node.__class__.__name__:
                            case 'Import':
                                for name in try_node.names:
                                    if name.name.split('.')[0] == package_name:
                                        if name.name not in custom_imports and turn_package_to_file(name.name) in file_list:
                                            custom_imports.append(name.name)
                                    else:
                                        if name.name[0] == '.':
                                            if len(name.name) > 1 and name.name[1] == '.':
                                                new_import = module_name[:module_name[:module_name.rfind('.')].rfind('.')] + name.name[1:]
                                                if new_import not in custom_imports and turn_package_to_file(new_import) in file_list:
                                                    custom_imports.append(new_import)
                                            else:
                                                new_import = module_name[:module_name.rfind('.')] + name.name
                                                if new_import not in custom_imports and turn_package_to_file(new_import) in file_list:
                                                    custom_imports.append(new_import)
                                import_statements.append(astor.to_source(try_node))
                            case 'ImportFrom':
                                if try_node.module == None:
                                    for name in try_node.names:
                                        new_import = module_name[:module_name.rfind('.')] + '.' + name.name
                                        if new_import not in custom_imports and turn_package_to_file(new_import) in file_list:
                                            custom_imports.append(new_import)
                                        new_import = module_name[:module_name[:module_name.rfind('.')].rfind('.')] + '.' + name.name
                                        if new_import not in custom_imports and turn_package_to_file(new_import) in file_list:
                                            custom_imports.append(new_import)
                                elif try_node.module.split('.')[0] == package_name:
                                    for name in try_node.names:
                                        new_import = try_node.module + '.' + name.name
                                        if new_import not in custom_imports and turn_package_to_file(new_import) in file_list:
                                            custom_imports.append(new_import)
                                import_statements.append(astor.to_source(try_node))
                            case 'Assign':
                                node_check = try_node.targets[0]

                                should_continue = False

                                for var_name in skip_assign:
                                    if node_check.__class__.__name__ == 'Name' and node_check.id == var_name:
                                        should_continue = True
                                        break
                                
                                if should_continue:
                                    continue

                                global_variables.append(astor.to_source(try_node))

        def process_class_body(nodes):
            global instance_vars
            for body_node in nodes:
                match body_node.__class__.__name__:
                    case 'Assign':
                        for target in body_node.targets:
                            if target.__class__.__name__ == 'Attribute':
                                instance_var = 'self.' + target.attr
                                if instance_var not in instance_vars:
                                    instance_vars.append(instance_var)
                                # file_stripped += '\t' + 'self.' + target.attr + '\n'
                    case 'If':
                        process_class_body(body_node.body)
                        process_class_body(body_node.orelse)
                    case 'For':
                        process_class_body(body_node.body)

        def process_file_body(nodes):
            global instance_vars, static_vars, methods, function_declarations, class_declarations, df, file_imports
            for node in nodes:
                match node.__class__.__name__:
                    case 'Try':
                        process_file_body(node.body)
                    case 'FunctionDef':
                        should_skip = False
                        for function_name in skip_functions:
                            if node.name == function_name:
                                should_skip = True
                                break
                        if should_skip:
                            continue

                        entry = {}
                        entry['filePath'] = f
                        entry['lineStart'] = node.lineno
                        entry['lineEnd'] = node.end_lineno
                        entry['numLines'] = entry['lineEnd'] - entry['lineStart'] + 1
                        entry['numParams'] = len(node.args.args)
                        entry['signature'] = ''
                        for decorator in node.decorator_list:
                            entry['signature'] += '@' + astor.to_source(decorator)
                        entry['signature'] += 'def ' + node.name + '('
                        for argument in node.args.args:
                            entry['signature'] += argument.arg + ', '
                        if len(node.args.args) != 0:
                            entry['signature'] = entry['signature'][:-2] + ')'
                        else:
                            entry['signature'] += ')'

                        entry['comment'] = ast.get_docstring(node)
                        if entry['comment'] != None:
                            entry['numCommentLines'] = entry['comment'].count('\n')
                        else:
                            entry['numCommentLines'] = 0
                        entry['content'] = astor.to_source(node)
                        entry['parentClass'] = None
                        entry['packageName'] = module_name
                        entry['imports'] = custom_imports
                        entry['repository'] = author + '/' + directory.split('/')[2]

                        string = entry['filePath'] + '--' + str(entry['lineStart']) + '--' + entry['signature'].rstrip('\n')
                        
                        hash_object = hashlib.sha256()
                        hash_object.update(string.encode('utf-8'))

                        entry['id'] = hash_object.hexdigest()

                        function_declarations.append((entry['signature'], entry['content'], entry['id']))

                        df = pd.concat([df, pd.DataFrame([entry])], axis=0, ignore_index=True)

                    case 'ClassDef':
                        instance_vars = []
                        methods = []
                        static_vars = []

                        class_name = node.name
                        class_signature = ''
                        for decorator in node.decorator_list:
                            class_signature += '@' + astor.to_source(decorator) + '\n'
                        class_signature += 'class ' + class_name + '('

                        for base in node.bases:
                            if base.__class__.__name__ == 'Attribute':
                                class_signature += astor.to_source(base)[:-1] + ', '
                            elif base.__class__.__name__ == 'Name':
                                class_signature += base.id + ', '

                        if len(node.bases) != 0:
                            class_signature = class_signature[:-2] + ')'
                        else:
                            class_signature += ')'

                        for class_node in node.body:
                            match class_node.__class__.__name__:
                                case 'Assign':
                                    static_vars.append(astor.to_source(class_node))
                                case 'FunctionDef':
                                    entry = {}
                                    entry['filePath'] = f
                                    entry['lineStart'] = class_node.lineno
                                    entry['lineEnd'] = class_node.end_lineno
                                    entry['numLines'] = entry['lineEnd'] - entry['lineStart'] + 1
                                    entry['numParams'] = len(class_node.args.args)
                                    entry['signature'] = ''
                                    for decorator in class_node.decorator_list:
                                        entry['signature'] += '@' + astor.to_source(decorator)
                                    entry['signature'] += 'def ' + class_node.name + '('
                                    for argument in class_node.args.args:
                                        entry['signature'] += argument.arg + ', '
                                    if len(class_node.args.args) != 0:
                                        entry['signature'] = entry['signature'][:-2] + ')'
                                    else:
                                        entry['signature'] += ')'
                                    
                                    # for line in entry['signature'].split('\n'):
                                    #     file_stripped += '\t' + line
                                    # file_stripped += '\n'
                                    entry['comment'] = ast.get_docstring(class_node)
                                    if entry['comment'] != None:
                                        entry['numCommentLines'] = entry['comment'].count('\n')
                                    else:
                                        entry['numCommentLines'] = 0
                                    entry['content'] = astor.to_source(class_node)
                                    entry['parentClass'] = class_name
                                    entry['packageName'] = module_name
                                    entry['imports'] = custom_imports
                                    entry['repository'] = author + '/' + directory.split('/')[2]
                                    
                                    string = entry['filePath'] + '--' + str(entry['lineStart']) + '--' + entry['signature'].rstrip('\n')

                                    hash_object = hashlib.sha256()
                                    hash_object.update(string.encode('utf-8'))

                                    entry['id'] = hash_object.hexdigest()

                                    methods.append((entry['signature'], entry['content'], entry['id']))

                                    process_class_body(class_node.body)
                                    df = pd.concat([df, pd.DataFrame([entry])], axis=0, ignore_index=True)

                        class_declaration = {
                            'className': class_signature,
                            'instanceVariables': instance_vars,
                            'methods': methods
                        }
                        class_declarations.append((class_declaration, astor.to_source(node)))

        process_file_body(t.body)

        file_imports[module_name] = {
            'importStatements': import_statements,
            'globalVariables': global_variables,
            'functionDeclarations': function_declarations,
            'classDeclarations': class_declarations
        }

df.to_json(f'./json_files/{package_name}_functions.json')

with open(f"./json_files/{package_name}_file_imports.json", "w") as outfile:
    json.dump(file_imports, outfile)