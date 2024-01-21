import os
import re
import json
import hashlib
import ast
import glob


def remove_spaces(text):
	if text is None:
		return ''
	return re.sub(r'\s+', '', text)

# Function to convert string to dictionary
# List{String} -> Dict{String: String}
# String = a:"b"
# Split by : and remove spaces
def list_to_dict(entries):
	# entries = [entry.strip() for entry in input_string.split(',')]

	result_dict = {}
	for entry in entries:
		# if the entry contains only spaces and new lines continue
		if remove_spaces(entry) == '':
			continue
		if ":" in entry:
			key, value = entry.split(':', 1)
			result_dict[key.strip()] = value

	return result_dict


# def list_to_dict(data):
# 	result = {}
# 	for item in data:
# 		result[item] = item
# 	return result

def parse_top_level_dict(content):
	brace_counter = 0
	current_key = ''
	top_level_dict = {}
	block_start_counter = None

	found_key = False
	i = 0
	while i < len(content):
		char = content[i]
		i += 1

		if char == '{':
			brace_counter += 1
			if brace_counter == 1:
				block_start_counter = i
		elif char == '}':
			brace_counter -= 1
			# Current key must not be empty
			if brace_counter == 0 and found_key == True and current_key != '':
				current_value_block = content[block_start_counter:i - 1].strip()
				top_level_dict[current_key] = current_value_block
				current_key = ''
				found_key = False
		elif char == ',':
			continue
		elif not char.isspace():
			if brace_counter == 0 and found_key == False:
				current_key = ''
				context = content[i - 1:]
				# Current key is the first word before the colon
				# Including [a-zA-Z0-9_]
				# Exclude punctuation
				# Search for the first word before the colon
				current_key = re.search(r'\b([a-zA-Z0-9_]+)\s*:', context).group(0)
				# Chop the : off the end
				current_key = current_key[:-1]
				found_key = True
				i = i + len(current_key) - 1

	return top_level_dict

# # Example usage:
# js_code = """
# SearchBar: {
#     alignItems: 'center',
#     alignContent: 'center',
#     justifyContent: 'flex-start',
#     margin: 20,
#     flexDirection: 'row',
#     elevation: 2,
#     shadowOffset: { width: 0, height: 1 },
#     shadowColor: '#000',
# },
# SearchButton: {
#     alignItems: 'center',
#     alignContent: 'center',
#     justifyContent: 'flex-start',
#     margin: 20,
#     flexDirection: 'row',
#     elevation: 2,
#     shadowColor: '#000',
# },
# """
#
# # Extract the top-level dictionary content
# top_level_dict = parse_top_level_dict(js_code)
#
# # Print the top-level dictionary
# print(top_level_dict)



def extract_styles_from_file(file_path):
	print(f"Extracting styles from {file_path}")
	with open(file_path, 'r') as file:
		content = file.read()
		match = re.search(r'StyleSheet\.create\s*\(\s*{([\s\S]*?)}\s*\)', content)
		styles_dict = {}
		if match:
			styles_content = match.group(1)
			styles_dict = parse_top_level_dict(styles_content)

			return styles_dict
		else:
			return {}


def hash_and_map_styles(styles_dict, filename, global_styles_name):
	filename_style_stylehash_hash_map = {}
	global_styles = {}

	for style_name, style_definition in styles_dict.items():
		style_string = json.dumps(style_definition, sort_keys=True)
		style_hash = hashlib.md5(style_string.encode()).hexdigest()
		if filename not in filename_style_stylehash_hash_map:
			filename_style_stylehash_hash_map[filename] = {}

		if style_name not in filename_style_stylehash_hash_map[filename]:
			filename_style_stylehash_hash_map[filename][style_name] = ''
		filename_style_stylehash_hash_map[filename][style_name] = style_hash

		if style_hash not in global_styles:
			global_styles[style_hash] = style_definition

	return filename_style_stylehash_hash_map, global_styles

def write_global_stylesheet(global_styles, output_file, global_styles_name):
	# global_styles_str = "const GlobalStyles = " + json.dumps(global_styles,
	# 																												 indent=2) + ";\n\nexport default GlobalStyles;"

	with open(output_file, 'w') as file:
		file.write('const ' + global_styles_name + " = {\n")
		for k,v in global_styles.items():
			file.write("  " + k + ": {\n    ")
			v_strip = v.strip()
			v_split = v_strip.split('\n')
			i = 0
			for i in range(len(v_split)):
				file.write(v_split[i] + "\n")
				# if i < len(v_split) - 1:
				# 	file.write(",")
				# file.write("\n")
			file.write("  },\n\n")

		file.write("}\n\nexport default GlobalStyles;")

#
# def replace_style_names_in_files(directory, style_map):
# 	for root, _, files in os.walk(directory):
# 		for file_name in files:
# 			if file_name.endswith('.js'):
# 				file_path = os.path.join(root, file_name)
# 				with open(file_path, 'r') as file:
# 					content = file.read()
#
# 				for hash_value, file_style_map in style_map.items():
# 					for file_name, local_style_names in file_style_map.items():
# 						for local_style_name in local_style_names:
# 							content = content.replace(f"{file_name}.{local_style_name}", f"GlobalStyles['{hash_value}']")
#
# 				with open(file_path, 'w') as file:
# 					file.write(content)


def add_import_to_file(file_path):
	with open(file_path, 'r') as file:
		content = file.read()

	import_statement = "import globalstyles from '../themes/HippoDefaultTheme';\n\n"

	with open(file_path, 'w') as file:
		file.write(import_statement + content)


def string_to_react_native_style_string(data_in):
	data_in_list = data_in.split('\n')
	result = ''
	for i in range(len(data_in_list)):
		result += data_in_list[i] + "\n"
	return result


# Write the global stylesheet to a file
def write_file_global_stylesheet(global_styles_map, output_global_stylesheet):
	global_styles_str = "const GlobalStyles = " + json.dumps(global_styles_map,
																													 indent=2) + ";\n\nexport default GlobalStyles;"
	with open(output_global_stylesheet, 'w') as file:
		for hash_value, style_definition in global_styles_map.items():
			#style_string = string_to_react_native_style_string(style_definition)
			style_list = style_definition.split('\n')
			file.write(f"const {hash_value} = ")
			for style in style_list:
				file.write(style + "\n")
			file.write("\n")


def write_style_map(style_map, directory_path):
	with open(directory_path + '/style_map.json', 'w') as file:
		file.write(json.dumps(style_map, indent=2))

def make_qualified_name(file_name, style_name):
	# Make the name with file_name + '.' + style_names[0] and remove .'s and spaces
	selected_name = re.sub(r'\.tsx', '', file_name)
	selected_name = re.sub(r'\.', '_', selected_name + '_' + style_name)
	return selected_name

# Create global stylesheet
#write_file_global_stylesheet(x, output_global_stylesheet)
def make_final_maps(style_map, global_styles_map):
	# Invert the style_map
	inverted_style_map = {}
	for file_name, file_style_map in style_map.items():
		for style_name, style_hash in file_style_map.items():
			if style_hash not in inverted_style_map:
				inverted_style_map[style_hash] = {}
			if file_name not in inverted_style_map[style_hash]:
				inverted_style_map[style_hash][file_name] = []
			inverted_style_map[style_hash][file_name].append(style_name)

	# Select a canonical style name for each style hash
	canonical_style_map = {}
	for style_hash, file_style_map in inverted_style_map.items():
		for file_name, style_names in file_style_map.items():
			selected_name = make_qualified_name(file_name, style_names[0])
			canonical_style_map[style_hash] = selected_name

	# Replace the hashes in the style_map with the canonical style names
	new_style_map = {}
	for file_name, file_style_map in style_map.items():
		new_style_map[file_name] = {}
		for style_name, style_hash in file_style_map.items():
			#selected_name = make_qualified_name(file_name, style_name)
			new_style_map[file_name][style_name] = canonical_style_map[style_hash]

	# Replace the hashes in the global stylesheet with the canonical style names
	new_global_styles_map = {}
	for style_hash, style_definition in global_styles_map.items():
		new_global_styles_map[canonical_style_map[style_hash]] = style_definition

	return new_style_map, new_global_styles_map

########################################################################################################################

directory_path = '/path to screens directory

# The name ofthe class to prefix styles with
global_styles_name = 'globalStyles'

# Write the global stylesheet to a file in the root directory
output_global_stylesheet = directory_path + '/GlobalStyles.ts'
style_map = {}
global_styles_map = {}

# # TEST ##########################################################
# file_path = "/Users/depappas/fix_styles/HippoApp/src/screens/Activity.tsx"
# styles_dict = extract_styles_from_file(file_path)
# file_name = os.path.basename(file_path)
# if styles_dict:
# 	style_hash_map, global_styles = hash_and_map_styles(styles_dict, file_name, global_styles_name)
# 	style_map.update(style_hash_map)
# 	global_styles_map.update(global_styles)
# 	new_style_map, new_global_styles_map = make_final_maps(style_map, global_styles_map)
# 	print()
# # END TEST ##########################################################
#

# for root, _, files in os.walk(directory_path):
# Define the pattern for matching styles
styles_pattern = re.compile(r'\bconst\s+styles\s*=\s*StyleSheet.create\({')

# Find files matching the pattern
matching_files = [file for file in glob.glob(f"{directory_path}/**/*.tsx", recursive=True) if
									styles_pattern.search(open(file).read())]

for file_path in matching_files:
	file_name = os.path.basename(file_path)
	print(f"Processing {file_name}")
	if file_name.endswith('.tsx'):
		#file_path = os.path.join(root, file_name)
		styles_dict = extract_styles_from_file(file_path)
		if styles_dict:
			style_hash_map, global_styles = hash_and_map_styles(styles_dict, file_name, global_styles_name)
			style_map.update(style_hash_map)
			global_styles_map.update(global_styles)


new_style_map, new_global_styles_map = make_final_maps(style_map, global_styles_map)

write_style_map(new_style_map, directory_path)

write_global_stylesheet(new_global_styles_map, output_global_stylesheet, global_styles_name)

print("Task completed successfully.")

