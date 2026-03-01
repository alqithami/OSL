#!/usr/bin/env python3
"""
NumPy Compatibility Fix for OSL Framework
Fixes the np.bool deprecation issue in newer NumPy versions
"""

import sys
import os
from pathlib import Path

def fix_numpy_compatibility():
    """Fix NumPy compatibility issues in the OSL codebase"""
    
    print("🔧 Fixing NumPy compatibility issues...")
    
    # Find the experiments/run.py file
    script_dir = Path(__file__).parent
    run_py_file = script_dir / 'experiments' / 'run.py'
    
    if not run_py_file.exists():
        print(f"❌ Could not find {run_py_file}")
        return False
    
    # Read the current content
    with open(run_py_file, 'r') as f:
        content = f.read()
    
    # Check if already fixed
    if 'hasattr(np, \'bool_\')' in content:
        print("✅ NumPy compatibility already fixed!")
        return True
    
    # Apply the fix
    old_code = '''            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, (bool, np.bool)):
                return bool(obj)'''
    
    new_code = '''            elif hasattr(np, 'bool_') and isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, bool):
                return bool(obj)'''
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        
        # Write the fixed content back
        with open(run_py_file, 'w') as f:
            f.write(content)
        
        print("✅ NumPy compatibility fixed!")
        print("   - Replaced deprecated np.bool with np.bool_")
        print("   - Added compatibility check for older NumPy versions")
        return True
    else:
        print("⚠️  Could not find the exact code pattern to fix.")
        print("   The file may have already been modified.")
        return False

def main():
    """Main function"""
    print("OSL NumPy Compatibility Fixer")
    print("=" * 40)
    
    success = fix_numpy_compatibility()
    
    if success:
        print("\n🎉 Fix applied successfully!")
        print("You can now run the tests again:")
        print("  python run_tests.py")
        return 0
    else:
        print("\n❌ Fix could not be applied automatically.")
        print("Please check the file manually.")
        return 1

if __name__ == '__main__':
    exit(main())

