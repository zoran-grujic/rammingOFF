import sys
import os
import re
import shutil

def read_gcode_settings(gcode_filepath):
    """
    Read gcode file and extract all settings after EXECUTABLE_BLOCK_END line.
    
    Args:
        gcode_filepath: Path to the input gcode file
        
    Returns:
        Dictionary with all extracted settings from the CONFIG_BLOCK.
        Values with commas are stored as lists, others as strings.
    """
    settings = {}
    
    executable_block_found = False
    config_block_end_found = False
    
    try:
        with open(gcode_filepath, 'r', encoding='utf-8') as f:
            for line in f:
                # Check if we've reached EXECUTABLE_BLOCK_END
                if 'EXECUTABLE_BLOCK_END' in line:
                    executable_block_found = True
                    continue
                
                # Check if we've reached CONFIG_BLOCK_END (stop reading)
                if 'CONFIG_BLOCK_END' in line:
                    config_block_end_found = True
                    break
                
                # Only process lines after EXECUTABLE_BLOCK_END
                if not executable_block_found:
                    continue
                
                # Skip empty lines and non-setting lines
                if not line.strip() or not line.startswith(';'):
                    continue
                
                # Extract settings (format: ; setting_name = value)
                match = re.match(r';\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)', line)
                if match:
                    setting_name = match.group(1).strip()
                    setting_value = match.group(2).strip()
                    
                    # Try to parse the value
                    # If it contains commas, split into a list
                    if ',' in setting_value:
                        # Try to convert to numbers if possible
                        try:
                            values = [float(v.strip()) if '.' in v else int(v.strip()) 
                                     for v in setting_value.split(',')]
                            settings[setting_name] = values
                        except ValueError:
                            # Keep as string list if conversion fails
                            settings[setting_name] = [v.strip() for v in setting_value.split(',')]
                    else:
                        # Try to convert to number if possible
                        try:
                            if '.' in setting_value:
                                settings[setting_name] = float(setting_value)
                            else:
                                settings[setting_name] = int(setting_value)
                        except ValueError:
                            # Keep as string if conversion fails
                            settings[setting_name] = setting_value
        
        if not executable_block_found:
            print("Warning: EXECUTABLE_BLOCK_END marker not found in file.")
        
        if not config_block_end_found:
            print("Warning: CONFIG_BLOCK_END marker not found in file.")
        
        return settings
        
    except FileNotFoundError:
        print(f"Error: File '{gcode_filepath}' not found.")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def process_gcode_for_filament_change(gcode_filepath, output_filepath):
    """
    Process gcode file for multi-color printing post-processing.
    
    Args:
        gcode_filepath: Path to the input gcode file
        output_filepath: Path to the output gcode file
    """
    # Step 1: Read settings from gcode file
    print(f"Reading settings from: {gcode_filepath}")
    settings = read_gcode_settings(gcode_filepath)
    
    if settings is None:
        print("Failed to read gcode file.")
        return
    
    # Display extracted settings summary
    print("\n=== Extracted Settings Summary ===")
    print(f"Total settings found: {len(settings)}")
    
    # Display key settings for multi-color printing
    key_settings = ['nozzle_temperature', 'chamber_temperature', 'first_layer_bed_temperature']
    for key in key_settings:
        if key in settings:
            print(f"{key}: {settings[key]}")
        else:
            print(f"{key}: NOT FOUND")
    
    print("==================================\n")
    
    # Check if required settings were found
    missing_settings = [k for k in key_settings if k not in settings]
    if missing_settings:
        print(f"Warning: Could not find the following required settings: {', '.join(missing_settings)}")
    
    # Step 2: Check if there are any ramming sections to process
    print(f"Checking for ramming sections...")
    
    try:
        with open(gcode_filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Count ramming sections
        ramming_count = sum(1 for line in lines if '; Ramming start' in line)
        
        if ramming_count == 0:
            print("No ramming sections found in gcode file.")
            print("No modifications needed - copying input to output...")
            # Copy input file to output file using OS-level copy (fast)
            shutil.copy2(gcode_filepath, output_filepath)
            print(f"File copied to: {output_filepath}")
            print("\nProcessing skipped.")
            return
        
        print(f"Found {ramming_count} ramming section(s) to process")
        print(f"Processing gcode file...")
        
        replacement_code = """; Ramming start
G91 ; Set positioning to relative (for Z-up lift)
G1 Z30 F600 ; Move Z-axis up by 30mm (adjust Z and F as needed)
G90 ; Set positioning back to absolute
QUIT_MATERIAL
; Cooling park"""
        
        # Step 2a: Replace ramming sections
        content = ''.join(lines)
        pattern = r'; Ramming start.*?; Cooling park'
        modified_content = re.sub(pattern, replacement_code, content, flags=re.DOTALL)
        
        # Step 2b: Insert Z-down after PAUSE commands (except for the last ramming section)
        modified_lines = modified_content.split('\n')
        output_lines = []
        
        # Find all "; Ramming end" positions
        ramming_end_positions = [i for i, line in enumerate(modified_lines) if '; Ramming end' in line]
        print(f"Found {len(ramming_end_positions)} ramming end marker(s)")
        
        # Process lines and insert Z-down code after PAUSE, and remove priming lines
        pause_insertions = 0
        skip_priming_lines_counter = 0  # Counter for skipping priming lines
        priming_sections_removed = 0
        
        for i, line in enumerate(modified_lines):
            # Check if we need to skip priming lines
            if '; CP TOOLCHANGE LOAD' in line:
                skip_priming_lines_counter = 6  # Skip this line and the next 5 lines
                priming_sections_removed += 1
                continue  # Skip the current line (the comment)
            
            if skip_priming_lines_counter > 0:
                skip_priming_lines_counter -= 1
                continue  # Skip the current line
            
            output_lines.append(line)
            
            # Check if this line contains PAUSE
            if 'PAUSE' in line:
                # Check if this PAUSE is within 10 lines after any "; Ramming end" (except the last one)
                for j, ramming_end_pos in enumerate(ramming_end_positions[:-1]):  # Exclude last one
                    if ramming_end_pos < i <= ramming_end_pos + 10:
                        # Insert Z-down compensation code
                        output_lines.append('G91 ; Set positioning to relative (for Z-down compensation)')
                        output_lines.append('G1 Z-30 F600 ; Move Z-axis down by 30mm (adjust Z and F as needed)')
                        output_lines.append('G90 ; Set positioning back to absolute')
                        
                        # Insert temperature setting for the next material
                        # j is the index of the current ramming section (0-based)
                        # j+1 gives us the next material index
                        next_material_index = j + 1

                        if settings['chamber_temperature'] and next_material_index < len(settings['chamber_temperature']):
                            next_chamber_temp = int(settings['chamber_temperature'][next_material_index])
                            output_lines.append(f'M141 S{next_chamber_temp} ; set chamber temperature for the new material')

                        if settings['nozzle_temperature'] and next_material_index < len(settings['nozzle_temperature']):
                            next_temp = int(settings['nozzle_temperature'][next_material_index])
                            output_lines.append(f'M104 S{next_temp} ; set temperature for the new material')          

                        if settings['first_layer_bed_temperature'] is not None:
                            bed_temp = int(settings['first_layer_bed_temperature'])
                            output_lines.append(f'M140 S{bed_temp} ; set initial bed temperature')
                            output_lines.append(f'M190 S{bed_temp} ; wait for bed temperature')

                        if settings['nozzle_temperature'] and next_material_index < len(settings['nozzle_temperature']):
                            output_lines.append(f'M109 S{next_temp} ; wait for nozzle temperature')  

                        
                            

                        
                        pause_insertions += 1
                        break  # Only insert once per PAUSE
        
        # Write the modified content to output file
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        
        print(f"Successfully replaced {ramming_count} ramming section(s)")
        print(f"Inserted Z-down compensation after {pause_insertions} PAUSE command(s)")
        print(f"Removed {priming_sections_removed} priming section(s) (CP TOOLCHANGE LOAD)")
        print(f"Output saved to: {output_filepath}")
        print("\nProcessing complete.")
        
    except Exception as e:
        print(f"Error processing gcode file: {e}")
        return




if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python your_script_name.py <input_gcode_file> [output_gcode_file]")
        print("If output_gcode_file is not provided, it will overwrite the input file.")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file

    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)

    process_gcode_for_filament_change(input_file, output_file)