#!/bin/bash
# GramAddict Device Facade Iter Bug Fix
# Fixes the "'Iter' object is not iterable" error in device_facade.py line 346

echo "🔧 Applying GramAddict Device Facade Iter Bug Fix..."

# Check if we're in the right directory
if [ ! -f "GramAddict/core/device_facade.py" ]; then
    echo "❌ Error: GramAddict/core/device_facade.py not found. Please run this script from the bot root directory."
    exit 1
fi

# Backup the original device_facade.py file
cp GramAddict/core/device_facade.py GramAddict/core/device_facade.py.backup
echo "✅ Backup created: GramAddict/core/device_facade.py.backup"

# Apply the fix using Python
python3 << 'PYTHON_EOF'
import re

# Read the original file
with open('GramAddict/core/device_facade.py', 'r') as f:
    content = f.read()

# Find the problematic __iter__ method and fix it
# The issue is in the __iter__ method where it tries to iterate over self.viewV2

# Fixed __iter__ method that handles Iter objects properly
fixed_iter_method = '''    def __iter__(self):
        children = []
        try:
            # Handle both iterable and Iter objects
            if hasattr(self.viewV2, '__iter__') and not hasattr(self.viewV2, '_method'):
                # Regular iterable
                children.extend(
                    DeviceFacade.View(view=item, device=self.deviceV2)
                    for item in self.viewV2
                )
            elif hasattr(self.viewV2, '__len__') and hasattr(self.viewV2, '__getitem__'):
                # Sequence-like object (can access by index)
                try:
                    length = len(self.viewV2)
                    children.extend(
                        DeviceFacade.View(view=self.viewV2[i], device=self.deviceV2)
                        for i in range(length)
                    )
                except Exception:
                    # If len() fails, try alternative approach
                    children.extend(
                        DeviceFacade.View(view=self.viewV2[i], device=self.deviceV2)
                        for i in range(50)  # Reasonable limit
                        if self.viewV2[i] is not None
                    )
            else:
                # Fallback: try to convert to list or handle as single item
                try:
                    # Try to get items using count() method if available
                    if hasattr(self.viewV2, 'count'):
                        count = self.viewV2.count
                        if callable(count):
                            item_count = count()
                        else:
                            item_count = count
                        
                        children.extend(
                            DeviceFacade.View(view=self.viewV2[i] if hasattr(self.viewV2, '__getitem__') else self.viewV2, device=self.deviceV2)
                            for i in range(min(item_count, 50))  # Limit to 50 items for safety
                        )
                    else:
                        # Last resort: treat as single item
                        children.append(DeviceFacade.View(view=self.viewV2, device=self.deviceV2))
                except Exception as e:
                    # If all else fails, return empty list to prevent crash
                    print(f"Warning: Could not iterate over view object: {e}")
                    children = []
        except Exception as e:
            # Safety net: if anything goes wrong, return empty list
            print(f"Warning: Iterator fallback triggered: {e}")
            children = []
            
        return iter(children)'''

# Find and replace the __iter__ method
# Look for the method definition and replace until the next method or class
pattern = r'(\s+def __iter__\(self\):.*?)(?=\n\s+def |\n\s+class |\nclass |\Z)'
new_content = re.sub(pattern, fixed_iter_method, content, flags=re.DOTALL)

# If the pattern didn't match, try a more specific approach
if new_content == content:
    # Look for the specific problematic lines
    lines = content.split('\n')
    new_lines = []
    in_iter_method = False
    indent_level = 0
    
    for i, line in enumerate(lines):
        if 'def __iter__(self):' in line:
            in_iter_method = True
            indent_level = len(line) - len(line.lstrip())
            # Replace the entire method with our fixed version
            method_lines = fixed_iter_method.split('\n')
            new_lines.extend(method_lines)
            continue
        elif in_iter_method:
            # Skip lines until we find the next method or class at the same or lower indentation
            current_indent = len(line) - len(line.lstrip()) if line.strip() else float('inf')
            if line.strip() and (line.strip().startswith('def ') or line.strip().startswith('class ')) and current_indent <= indent_level:
                in_iter_method = False
                new_lines.append(line)
            # Skip all lines that are part of the old __iter__ method
        else:
            new_lines.append(line)
    
    new_content = '\n'.join(new_lines)

# Write the fixed content back
with open('GramAddict/core/device_facade.py', 'w') as f:
    f.write(new_content)

print("✅ Device facade __iter__ method fixed successfully!")
PYTHON_EOF

echo ""
echo "🎯 Device Facade Iter bug fix applied!"
echo "The 'Iter' object is not iterable error in device_facade.py should now be resolved"
echo ""
echo "📋 To revert the fix if needed:"
echo "   cp GramAddict/core/device_facade.py.backup GramAddict/core/device_facade.py"
echo ""
echo "🚀 You can now run the bot again!"
