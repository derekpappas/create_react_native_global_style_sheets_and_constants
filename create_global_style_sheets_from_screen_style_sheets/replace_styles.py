import os
import re
import json
import subprocess

def read_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading JSON file {file_path}: {e}")
        return None

def write_to_file(file_path, content):
    try:
        with open(file_path, 'w') as file:
            file.write(content)
    except IOError as e:
        print(f"Error writing to file {file_path}: {e}")

def process_react_native_file(file_path, global_styles_import, file_style_map, new_prefix):
    old_prefix = 'styles.'
    try:
        with open(file_path, 'r') as file:
            content = file.read()

        if "StyleSheet.create" in content:
            # Add import statement after header comment */
            content = re.sub(r'(\*/)', r'\1\n' + global_styles_import, content)

            for local_style_name, global_style_name in file_style_map.items():
                # Replace local style occurrences
                content = re.sub(r'style\s*=\s*{\s*' + re.escape(old_prefix) + local_style_name + r'\s*}', r'style={' + new_prefix + '.' + global_style_name + r'}', content)
                content = re.sub(re.escape(old_prefix) + local_style_name, new_prefix + '.' + global_style_name, content)

            # Replace filename:style occurrences

            # Remove everything on and after const styles = StyleSheet.create except the export at the end of the file
            pattern = re.compile(r'\bconst\s+styles\s*=\s*StyleSheet\.create\([^)]*\)', re.DOTALL)
            code_without_styles = pattern.sub('', content)
            return code_without_styles

    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None


def sdiff(file1, file2, output_file):
    def strip_ansi(text):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    # Run sdiff and colordiff using subprocess
    try:
        # Run sdiff and colordiff, redirecting the output to the diff file
        sdiff_process = subprocess.run(["sdiff", "-s", file1, file2], stdout=subprocess.PIPE, text=True)
        colordiff_output = subprocess.run(["colordiff"], input=sdiff_process.stdout, stdout=subprocess.PIPE, text=True)

        # Strip ANSI escape codes before saving to the output file
        stripped_output = strip_ansi(colordiff_output.stdout)

        # Save the stripped colored diff to the output file
        with open(output_file, 'w') as diff_file:
            diff_file.write(stripped_output)

        print(f"Colored diff saved to {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
def process_files_in_directory(directory_path, style_map):
    global_styles_name = "globalStyles"


    for root, dirs, files in os.walk(directory_path):
        # Sort files so that the order is consistent
        files = sorted(files)
        i = 0
        for file in files:
            if file.endswith(".tsx"):
                file_path = os.path.join(root, file)
                # element_id = os.path.basename(root)
                if file in style_map:
                    file_style_map = style_map[file]
                    if file_style_map:
                        # compare the number of levels in the path to the number of os.sep in the root
                        # compute a number of ../ to add to the import statement
                        root_count = root.count(os.sep)
                        directory_path_count = directory_path.count(os.sep)
                        level = root_count - directory_path_count
                        # Add the appropriate number of ../ to the import statement
                        relative_path = "../" * level + "../GlobalStyles"
                        global_styles_import = "import " + global_styles_name + " from '" + relative_path +'";';
                        modified_content = process_react_native_file(file_path, global_styles_import, file_style_map, global_styles_name)
                        if modified_content:
                            file_path_copy = file_path + ".copy5"
                            write_to_file(file_path_copy, modified_content)
                            print(f"Processed file: {file_path}")
                            # sdiff -s file_path file_path_copy | colordiff > file_path.diff
                            sdiff(file_path, file_path_copy, file_path + ".diff")





root_dir = '/path to screens directory
# Read style_map.json
style_map_path = root_dir + "/style_map.json"
style_map = read_json_file(style_map_path)

# Specify the directory containing your React Native tsx files
directory_path = root_dir

# Process files in the directory
if style_map:
    process_files_in_directory(directory_path, style_map)
