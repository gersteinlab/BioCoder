import ast
import astor
import os
import pandas as pd
import json

directory = 'pymbar/pymbar'
package_name = 'pymbar'

skip_dirs = ['tests', 'testsystems', '__pycache__', 'exampledata']
skip_files = ['__init__.py', '_version.py', 'utils_for_testing.py', 'GUI.py', 'citation.py', 'version.py', 'basedir.py']
skip_assign = ['__authors__', '__license__', 'LongWarning', '__credits', '__credits__', '__email__', 'SCOARY_VERSION', '__author__']

df = pd.DataFrame(columns=['filePath', 'numLines', 'lineStart', 'lineEnd', 'numParams', 'signature', 'comment', 'numCommentLines', 'content', 'parentClass', 'packageName', 'imports'])

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

        import_list = []

        assignment_list = []

        import_statements = ''

        module_name = package_name

        for item in f[(len(directory) + 1):].split('/'):
            module_name += '.' + item

        module_name = module_name[:-3]

        for node in t.body:
            match node.__class__.__name__:
                case 'Import':
                    for name in node.names:
                        if name.name.split('.')[0] == package_name and name.name != package_name:
                            if name.name not in import_list and turn_package_to_file(name.name) in file_list:
                                import_list.append(name.name)
                        else:
                            if name.name[0] == '.':
                                new_import = module_name[:module_name.rfind('.')] + name.name
                                if new_import not in import_list and turn_package_to_file(new_import) in file_list:
                                    import_list.append(new_import)
                    import_statements += (astor.to_source(node)) + '\n'
                case 'ImportFrom':
                    if node.module.split('.')[0] == package_name:
                        for name in node.names:
                            new_import = node.module + '.' + name.name
                            if new_import not in import_list and turn_package_to_file(new_import) in file_list:
                                import_list.append(new_import)
                        if node.module not in import_list and turn_package_to_file(node.module) in file_list:
                            import_list.append(node.module)
                    else:
                        import_line = astor.to_source(node)
                        new_import = module_name[:module_name.rfind('.')]  + '.' + node.module
                        if import_line.split(' ')[1][0] == '.':
                            if new_import not in import_list and turn_package_to_file(new_import) in file_list:
                                import_list.append(new_import)
                    import_statements += (astor.to_source(node)) + '\n'
                case 'Assign':
                    node_check = node.targets[0]

                    should_continue = False

                    for var_name in skip_assign:
                        if node_check.__class__.__name__ == 'Name' and node_check.id == var_name:
                            should_continue = True
                            break
                    
                    if should_continue:
                        continue

                    assignment_list.append(astor.to_source(node))
                case 'Try':
                    for try_node in node.body:
                        match try_node.__class__.__name__:
                            case 'Import':
                                for name in try_node.names:
                                    if name.name.split('.')[0] == package_name and name.name != package_name:
                                        if name.name not in import_list and turn_package_to_file(name.name) in file_list:
                                            import_list.append(name.name)
                                    else:
                                        if name.name[0] == '.':
                                            new_import = module_name[:module_name.rfind('.')] + name.name
                                            if new_import not in import_list:
                                                import_list.append(new_import)
                                    import_statements += (astor.to_source(try_node)) + '\n'
                            case 'ImportFrom':
                                if try_node.module.split('.')[0] == package_name:
                                    for name in try_node.names:
                                        new_import = try_node.module + '.' + name.name
                                        if new_import not in import_list:
                                            import_list.append(new_import)
                                    if try_node.module not in import_list and turn_package_to_file(try_node.module) in file_list:
                                        import_list.append(try_node.module)
                                else:
                                    import_line = astor.to_source(try_node)
                                    new_import = module_name[:module_name.rfind('.')]  + '.' + try_node.module
                                    if import_line.split(' ')[1][0] == '.':
                                        if new_import not in import_list:
                                            import_list.append(new_import)
                                import_statements += (astor.to_source(try_node)) + '\n'
                            case 'Assign':
                                node_check = try_node.targets[0]

                                should_continue = False

                                for var_name in skip_assign:
                                    if node_check.__class__.__name__ == 'Name' and node_check.id == var_name:
                                        should_continue = True
                                        break
                                
                                if should_continue:
                                    continue

                                assignment_list.append(astor.to_source(try_node))

        function_signatures = []

        global instance_vars
        instance_vars = []
        file_stripped = ''

        for assignment in assignment_list:
            file_stripped += assignment + '\n'

        def process_body(nodes):
            for body_node in nodes:
                match body_node.__class__.__name__:
                    case 'Assign':
                        for target in body_node.targets:
                            if target.__class__.__name__ == 'Attribute':
                                global instance_vars
                                instance_var = 'self.' + target.attr
                                if instance_var not in instance_vars:
                                    instance_vars.append(instance_var)
                                # file_stripped += '\t' + 'self.' + target.attr + '\n'
                    case 'If':
                        process_body(body_node.body)
                        process_body(body_node.orelse)
                    case 'For':
                        process_body(body_node.body)

        for node in t.body:
            match node.__class__.__name__:
                case 'FunctionDef':
                    entry = {}
                    entry['filePath'] = f
                    entry['lineStart'] = node.lineno
                    entry['lineEnd'] = node.end_lineno
                    entry['numLines'] = entry['lineEnd'] - entry['lineStart'] + 1
                    entry['numParams'] = len(node.args.args)
                    entry['signature'] = ''
                    for decorator in node.decorator_list:
                        entry['signature'] += '@' + astor.to_source(decorator) + '\n'
                    entry['signature'] += 'def ' + node.name + '('
                    for argument in node.args.args:
                        entry['signature'] += argument.arg + ', '
                    if len(node.args.args) != 0:
                        entry['signature'] = entry['signature'][:-2] + ')'
                    else:
                        entry['signature'] += ')'
                    file_stripped += entry['signature'] + '\n'
                    entry['comment'] = ast.get_docstring(node)
                    if entry['comment'] != None:
                        entry['numCommentLines'] = entry['comment'].count('\n')
                    else:
                        entry['numCommentLines'] = 0
                    entry['content'] = astor.to_source(node)
                    entry['parentClass'] = None
                    entry['packageName'] = module_name
                    entry['imports'] = import_list
                    df = pd.concat([df, pd.DataFrame([entry])], axis=0, ignore_index=True)

                case 'ClassDef':
                    class_name = node.name
                    class_signature = ''
                    for decorator in node.decorator_list:
                        class_signature += '@' + astor.to_source(decorator) + '\n'
                    class_signature += 'class ' + class_name + '('
                    for base in node.bases:
                        if base.__class__.__name__ == 'Attribute':
                            class_signature += base.value.id + '.' + base.attr + ', '
                        elif base.__class__.__name__ == 'Name':
                            class_signature += base.id + ', '
                    if len(node.bases) != 0:
                        class_signature = class_signature[:-2] + ')'
                    else:
                        class_signature += ')'
                    file_stripped += class_signature + '\n'

                    function_sigs = []

                    for class_node in node.body:
                        match class_node.__class__.__name__:
                            case 'Assign':
                                file_stripped += '\t' + astor.to_source(class_node) + '\n'
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
                                function_sigs.append(entry['signature'])
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
                                entry['imports'] = import_list
                                process_body(class_node.body)
                                df = pd.concat([df, pd.DataFrame([entry])], axis=0, ignore_index=True)

                    for instance_var in instance_vars:
                        file_stripped += '\t' + instance_var + '\n'

                    for function_sig in function_sigs:
                        for line in function_sig.split('\n'):
                            file_stripped += '\t' + line + '\n'


        file_imports[module_name] = file_stripped, import_statements

df.to_json(f'../json_files/{package_name}_functions.json')

with open(f"../json_files/{package_name}_file_imports.json", "w") as outfile:
    json.dump(file_imports, outfile)