# rammingOFF - OrcaSlicer Multi-Material Post-Processing Script

A post-processing script for OrcaSlicer that optimizes multi-color/multi-material gcode for single-extruder 3D printers with manual filament changes.

---

## ⚠️ Disclaimer

**USE AT YOUR OWN RISK**

This software is provided "as is", without warranty of any kind, express or implied. The author(s) and contributors assume no responsibility for any damage, injury, loss, or other consequences arising from the use or misuse of this script, including but not limited to:

- Damage to 3D printer hardware or components
- Failed prints or wasted materials
- Fire hazards or safety incidents
- Data loss or corruption
- Any other direct or indirect damages

**By using this script, you acknowledge that:**
- You understand the risks involved in modifying gcode
- You are responsible for testing thoroughly with your specific printer and configuration
- You accept full responsibility for monitoring your printer during operation
- You should always supervise your 3D printer while printing, especially during toolchanges
- The author(s) provide this tool as-is with no guarantees of fitness for any particular purpose

**Always test with small, non-critical prints first and monitor the first several toolchanges closely.**

---

## Overview

This script addresses critical issues with OrcaSlicer's default multi-material gcode generation when used with single-extruder printers that lack automated filament management systems (like Bambu Lab AMS or Creality CFS).

### The Problem

When slicing multi-material prints with OrcaSlicer for manual filament changes, the generated gcode includes:
- **Automatic ramming sequences** designed for MMU systems that cause material waste
- **Automated priming routines** that extrude ~90mm of filament per toolchange
- **Inadequate Z-axis positioning** during filament changes
- **Risk of filament jamming** due to unadequate filament load/unload implementation, unnecessary extrusion and retraction cycles

These issues result in:
- ❌ Significant material waste
- ❌ Extremely high probability of extruder jamming
- ❌ Print failures during toolchanges
- ❌ Poor user experience with manual multi-material printing

### The Solution

**rammingOFF** modifies the gcode to:
- ✅ Replace OrcaSlicer's ramming sequences with custom macros (e.g., `QUIT_MATERIAL`)
- ✅ Remove automatic priming routines (saves ~90mm filament per toolchange)
- ✅ Add proper Z-axis compensation for better filament accessibility
- ✅ Insert temperature management commands for the next material
- ✅ Optimize toolchange workflow for manual filament changes

## Developed For

- **Printer**: Creality K1C (and similar Klipper-based printers)
- **Slicer**: OrcaSlicer
- **Use Case**: Multi-material prints with Prime Tower on single-extruder printers

## Features

- 🔧 **Replaces ramming sequences** with your custom `QUIT_MATERIAL` macro
- 🗑️ **Removes wasteful priming** (~90mm of filament saved per toolchange)
- 📏 **Adds Z-lift compensation** (configurable, default +30mm/-30mm)
- 🌡️ **Manages temperatures** for next material automatically
- ⚡ **Smart detection** - skips processing if no multi-material toolchanges detected
- 🚀 **Fast processing** - uses OS-level file copy when no changes needed

## Installation

### Step 1: Download the Script

Copy `rammingOFF.py` to a folder on your computer.

**Windows example**:
```
C:\Users\YourName\3DPrinting\rammingOFF.py
```

**Linux example**:
```bash
mkdir -p ~/3DPrinting
# Copy or download the script to:
~/3DPrinting/rammingOFF.py
```

**Optional - Make executable (Linux only)**:
```bash
chmod +x ~/3DPrinting/rammingOFF.py
```

### Step 2: Configure OrcaSlicer

1. Open **OrcaSlicer**
2. Go to **Process** → **Others** → **Post-processing Scripts**
3. Add the appropriate line for your operating system:

   **Windows**:
   ```
   python "C:\Users\YourName\3DPrinting\rammingOFF.py";
   ```
   
   **Windows (Anaconda)**:
   ```
   "C:\Users\YourName\anaconda3\python.exe" "C:\Users\YourName\3DPrinting\rammingOFF.py";
   ```
   
   **Linux**:
   ```bash
   python3 /home/username/3DPrinting/rammingOFF.py;
   ```
   
   **Linux (with full path)**:
   ```bash
   /usr/bin/python3 /home/username/3DPrinting/rammingOFF.py;
   ```

   ⚠️ **Important**: 
   - Use the full path to your Python executable if `python`/`python3` is not in your system PATH
   - **Windows**: Use forward slashes `/` or escaped backslashes `\\` in the path
   - **Linux**: Use forward slashes `/` (standard)
   - Don't forget the semicolon `;` at the end

4. Click **OK** to save

### Step 3: Configure PAUSE Macro (Highly Recommended)

To improve accessibility during filament changes and reduce jamming risk, modify your printer's PAUSE macro to park the extruder in the **center of the XY plane** instead of the front-left corner.

#### For Klipper-Based Printers (K1C, etc.):

1. **Access the configuration file**:
   
   **Option A: SSH (Linux/macOS/Windows with SSH client)**
   ```bash
   ssh root@<printer-ip>
   ```
   
   **Option B: Web Interface (All platforms)**
   - Open browser: `http://<printer-ip>`
   - Navigate to: Fluidd/Mainsail → Configuration tab

2. **Edit the PAUSE macro**:
   - **File location (K1C)**: `/usr/data/printer_data/config/gcode_macro.cfg`
   - **Find the section**: `[gcode_macro PAUSE]`
   
   **Linux/macOS command**:
   ```bash
   ssh root@<printer-ip>
   nano /usr/data/printer_data/config/gcode_macro.cfg
   ```
   
   **Or use web interface editor** (works on all platforms)

3. **Set center parking position**:
   ```gcode
   [gcode_macro PAUSE]
   description: Pause the actual running print
   rename_existing: PAUSE_BASE
   gcode:
       # Calculate center position
       {% set y_park = printer.toolhead.axis_maximum.y/2 %}
       {% set x_park = printer.toolhead.axis_maximum.x/2 %}
       
       # Rest of your PAUSE macro...
       PAUSE_BASE
       G91
       G1 E-1 F2100
       G1 Z10 F900
       G90
       G1 X{x_park} Y{y_park} F6000
   ```

4. **Save and restart Klipper**

#### Why Center Parking?

- 🔧 **Easy extruder access** - No need to reach to the back or sides
- 🛠️ **Better serviceability** - If jamming occurs, the extruder assembly is easily accessible
- 🎯 **Consistent positioning** - Same location for all toolchanges
- ⚙️ **Works for all bed sizes** - Automatically calculates center position

## Usage

1. **Slice your multi-material print** in OrcaSlicer as usual
2. **Use a Prime Tower** for color transitions
3. **Export the gcode** (the script runs automatically during export)
4. **Print!**

### During Printing

When a toolchange occurs:
1. Printer executes Z-lift (+30mm by default)
2. Runs `QUIT_MATERIAL` macro (your custom unload routine)
3. Pauses at center position (if configured)
4. **You manually change filament**
5. Printer executes Z-down compensation (-30mm)
6. Sets temperature for new material
7. Resumes printing

## What the Script Modifies

### Before (OrcaSlicer default):
```gcode
; Ramming start
G1 E-15.0000 F6000
G1 E-55.3000 F5400
; ... (many ramming moves)
; Cooling
G1 X140.007 E5.0000 F475
; ... (cooling moves)
; Cooling park

PAUSE

; CP TOOLCHANGE LOAD
G1 E18.0000 F180        ; Prime 18mm
G1 X139.882 E63.0000    ; Prime 63mm
G1 X158.007 E9.0000     ; Prime 9mm more
; ... (continues printing)
```

### After (rammingOFF processed):
```gcode
; Ramming start
G91 ; Set positioning to relative
G1 Z30 F600 ; Z-lift for clearance
G90 ; Set positioning back to absolute
QUIT_MATERIAL ; Your custom macro
; Cooling park

PAUSE
G91 ; Set positioning to relative
G1 Z-30 F600 ; Z-down compensation
G90 ; Set positioning back to absolute
M104 S250 ; Set temperature for next material

; ... (priming section removed, continues printing)
```

**Result**: ~90mm less filament wasted, no jamming from excessive ramming!

## Requirements

- **Python 3.6+** (with standard library only, no external dependencies)
  - Windows: Python 3.6+ or Anaconda
  - Linux: `python3` (usually pre-installed on modern distributions)
  - macOS: Python 3.6+ (install via Homebrew or python.org)
- **OrcaSlicer** (tested with v2.x)
- **Single-extruder 3D printer** (tested on Creality K1C)
- **Klipper firmware recommended** (for custom macros support)

### Platform Compatibility
✅ **Windows** 7/10/11  
✅ **Linux** (Ubuntu, Debian, Fedora, Arch, etc.)  
✅ **macOS** (Intel and Apple Silicon)  

The script uses only Python standard library and is fully cross-platform.

## Customization

### Adjusting Z-Lift Values

If you need to change the Z-lift/Z-down amounts, edit the script:

```python
replacement_code = """; Ramming start
G91 ; Set positioning to relative (for Z-up lift)
G1 Z20 F600 ; Change Z30 to your desired value
G90 ; Set positioning back to absolute
QUIT_MATERIAL
; Cooling park"""
```

And update the Z-down compensation:
```python
output_lines.append('G1 Z-20 F600 ; Change Z-30 to match your Z-up value')
```

### Custom Macro Name

Replace `QUIT_MATERIAL` with your preferred macro name:
```python
QUIT_MATERIAL  # Change to YOUR_MACRO_NAME
```

## Troubleshooting

### Script Not Running

**Windows**:
- Verify Python is in your PATH or use full path to `python.exe`
- Check the semicolon `;` at the end of the post-processing script line
- Look for errors in OrcaSlicer's console output
- Try using forward slashes `/` instead of backslashes `\` in paths

**Linux**:
- Use `python3` instead of `python` (most distributions)
- Verify Python is installed: `python3 --version`
- Check file permissions: `ls -la rammingOFF.py`
- Make executable if needed: `chmod +x rammingOFF.py`
- Check the semicolon `;` at the end of the post-processing script line

**All Platforms**:
- Test the script manually from terminal/command prompt:
  ```bash
  python3 rammingOFF.py input.gcode output.gcode  # Linux/macOS
  python rammingOFF.py input.gcode output.gcode   # Windows
  ```

### Z-Height Issues After Toolchange
- Your PAUSE macro may have its own Z-lift
- Adjust script's Z values to compensate
- See: [K1C PAUSE Configuration](./K1C_PAUSE_LOCATION.md)

### Temperature Not Set Correctly
- Script reads `nozzle_temperature` from gcode settings
- Verify your filament temperature settings in OrcaSlicer
- Check output gcode for `M104` commands after PAUSE

### Material Still Jamming
- Ensure PAUSE parks at center position for easy access
- Check that `QUIT_MATERIAL` properly unloads filament
- Verify retraction settings aren't too aggressive
- Consider increasing Z-lift value in script

### File Path Issues (Linux)
- Ensure you use absolute paths: `/home/username/...` not `~/...`
- Or use full expansion: `/home/$USER/3DPrinting/rammingOFF.py`
- Check file permissions: File should be readable (`-rw-r--r--` or `-rwxr-xr-x`)
- Verify Python location: `which python3` shows the correct path

### SSH Access to Printer (Linux/macOS)
```bash
# Install SSH client if needed (usually pre-installed)
sudo apt install openssh-client  # Debian/Ubuntu
sudo dnf install openssh-clients # Fedora

# Connect to printer
ssh root@192.168.1.100  # Replace with your printer's IP
```

## Platform-Specific Notes

### Linux Users

**Finding Python**:
```bash
which python3          # Shows Python location (usually /usr/bin/python3)
python3 --version      # Verify version (should be 3.6+)
```

**Installing Python (if needed)**:
```bash
# Debian/Ubuntu
sudo apt update
sudo apt install python3

# Fedora/RHEL
sudo dnf install python3

# Arch Linux
sudo pacman -S python
```

**File Locations**:
- User directory: `/home/username/3DPrinting/`
- System-wide: `/usr/local/bin/` (requires sudo)
- Recommended: Use user directory for easy access

**Permissions**:
```bash
# Make script executable (optional)
chmod +x ~/3DPrinting/rammingOFF.py

# Then call directly (if shebang added)
~/3DPrinting/rammingOFF.py input.gcode output.gcode
```

### Windows Users

**Finding Python**:
```cmd
where python           # Shows Python location
python --version       # Verify version
```

**Common Python Locations**:
- User install: `C:\Users\YourName\AppData\Local\Programs\Python\Python3XX\python.exe`
- Anaconda: `C:\Users\YourName\anaconda3\python.exe`
- System install: `C:\Python3XX\python.exe`

### macOS Users

**Finding Python**:
```bash
which python3          # Shows Python location
python3 --version      # Verify version
```

**Installing Python (via Homebrew)**:
```bash
brew install python3
```

## Technical Details

The script performs the following operations:

1. **Settings Extraction**: Reads all slicer settings from gcode CONFIG_BLOCK
2. **Ramming Detection**: Checks for `; Ramming start` markers
3. **Ramming Replacement**: Replaces entire ramming sequence with custom macro
4. **Z-Compensation**: Adds Z-up before and Z-down after PAUSE
5. **Priming Removal**: Removes 6 lines of `CP TOOLCHANGE LOAD` sequence
6. **Temperature Management**: Inserts M-codes for next material temperature
7. **Smart Skip**: If no ramming detected, uses fast OS-level file copy

For detailed technical documentation, see:
- [COMPARISON.md](./COMPARISON.md) - Comparison with original version
- [PRIMING_EXPLANATION.md](./PRIMING_EXPLANATION.md) - Details on priming removal
- [XY_POSITION_ANALYSIS.md](./XY_POSITION_ANALYSIS.md) - Position tracking analysis

## Contributing

Issues, suggestions, and pull requests are welcome! This script was developed to solve a specific problem with K1C + OrcaSlicer, but should work with similar setups.

### How to Contribute

1. **Fork the repository** and create a feature branch
2. **Test your changes** thoroughly with your printer setup
3. **Document your changes** in code comments and README if needed
4. **Submit a pull request** with a clear description of improvements
5. **Add yourself to credits** if you make significant contributions

## License

**MIT License**

Copyright (c) 2025 Zoran D. Grujić ([@zoran-grujic](https://github.com/zoran-grujic))

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Credits

### Original Author
- **Zoran D. Grujić** ([@zoran-grujic](https://github.com/zoran-grujic)) - Initial development and release (2025)

### Contributors
*Contributors who improve this project are welcomed to add their names here*

### Acknowledgments
- Developed for the 3D printing community
- Created to solve multi-material challenges with Creality K1C and OrcaSlicer
- Inspired by the need for reliable manual multi-material printing

**Note**: This is a community tool. Always test with small prints first and monitor the first few toolchanges to ensure proper operation with your specific printer and configuration.
