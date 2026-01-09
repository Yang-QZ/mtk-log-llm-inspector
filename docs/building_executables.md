# Building and Distributing Executables

This guide explains how to build standalone executables for MTK Log LLM Inspector and distribute them to users who don't have Python installed.

## Prerequisites

- Python 3.8 or higher
- PyInstaller (`pip install pyinstaller`)
- All project dependencies installed (`pip install -r requirements.txt`)

## Building the Executable

### Quick Build

**Windows:**
```cmd
build_exe.bat
```

**Linux/Mac:**
```bash
./build_exe.sh
```

The build script will:
1. Check if PyInstaller is installed (and install it if needed)
2. Clean any previous builds
3. Build the executable using the `mtk_log_inspector.spec` file
4. Output the result to the `dist/` directory

### Manual Build

If you prefer to build manually:

```bash
pyinstaller --clean --noconfirm mtk_log_inspector.spec
```

## Output

After a successful build, you'll find the executable in:

- **Windows:** `dist/MTK_Log_Inspector.exe` (~15-30 MB)
- **Linux:** `dist/MTK_Log_Inspector` (~15-30 MB)
- **macOS:** `dist/MTK_Log_Inspector` (~15-30 MB)

## Distribution Package

When distributing the executable to end users, include:

1. The executable file (`MTK_Log_Inspector.exe` or `MTK_Log_Inspector`)
2. `EXECUTABLE_README.md` (renamed to `README.txt` or `README.md`)
3. (Optional) Sample log files from `samples/` directory

### Creating a Release Package

**Windows (ZIP):**
```cmd
mkdir release
copy dist\MTK_Log_Inspector.exe release\
copy EXECUTABLE_README.md release\README.txt
copy samples\*.log release\samples\
cd release
tar -a -c -f MTK_Log_Inspector_Windows_v1.0.0.zip *
```

**Linux/Mac (tar.gz):**
```bash
mkdir release
cp dist/MTK_Log_Inspector release/
cp EXECUTABLE_README.md release/README.md
cp -r samples release/
cd release
tar -czf MTK_Log_Inspector_Linux_v1.0.0.tar.gz *
```

## Platform-Specific Notes

### Windows

- The executable is built as a GUI application (no console window)
- Windows Defender or other antivirus software may flag the executable as suspicious initially
- Users may need to click "More info" → "Run anyway" when running for the first time
- The executable works on Windows 7 and later

### Linux

- The executable requires the same Linux distribution family (Debian/Ubuntu, RedHat/Fedora, etc.)
- Users need to make the file executable: `chmod +x MTK_Log_Inspector`
- May require display server (X11/Wayland) for tkinter GUI

### macOS

- The executable may be blocked by Gatekeeper
- Users need to right-click → "Open" or use `xattr -d com.apple.quarantine MTK_Log_Inspector`
- Alternatively, build a proper .app bundle or .dmg file for distribution

## Customization

### Changing the Icon

1. Create an `.ico` file (Windows) or `.icns` file (macOS)
2. Update `mtk_log_inspector.spec`:
   ```python
   exe = EXE(
       ...
       icon='path/to/icon.ico',  # Add this line
   )
   ```
3. Rebuild the executable

### Changing the Executable Name

Edit `mtk_log_inspector.spec` and modify the `name` parameter:
```python
exe = EXE(
    ...
    name='MyCustomName',
    ...
)
```

### Including Additional Files

To include additional data files, modify the `datas` list in `mtk_log_inspector.spec`:
```python
docs_datas = [
    ('docs/prompt.md', 'docs'),
    ('path/to/your/file.txt', 'destination/folder'),
]
```

## Troubleshooting

### Build Errors

**Issue: "Module not found" errors**
- Solution: Add missing modules to `hiddenimports` in the spec file

**Issue: "tkinter not found" warnings**
- On Linux: Install `python3-tk` package
- On Windows: Reinstall Python with tcl/tk support

**Issue: Large executable size**
- Solution: Use `excludes` in the spec file to exclude unnecessary modules
- Consider using `--onefile` mode (already enabled in the spec)

### Runtime Errors

**Issue: "Failed to execute script" error**
- Run in console mode temporarily to see error messages
- Change `console=False` to `console=True` in the spec file

**Issue: Missing data files**
- Verify all required files are in the `datas` list
- Check paths are correct (relative to project root)

**Issue: Import errors at runtime**
- Add missing imports to `hiddenimports` in the spec file

## Testing the Executable

Before distribution, test the executable on a clean system:

1. **Fresh Windows/Linux VM** without Python installed
2. **Run basic operations:**
   - Launch the application
   - Load a sample log file
   - Configure API key (use a test key)
   - Run a small analysis
   - Save results

3. **Check for:**
   - Missing dependencies
   - File path issues
   - Permission problems
   - UI rendering issues

## GitHub Releases

To create a GitHub release with the executable:

1. Tag your release:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

2. Go to GitHub → Releases → "Create a new release"

3. Upload the executables:
   - `MTK_Log_Inspector_Windows_v1.0.0.zip`
   - `MTK_Log_Inspector_Linux_v1.0.0.tar.gz`
   - `MTK_Log_Inspector_macOS_v1.0.0.tar.gz`

4. Include release notes with:
   - New features
   - Bug fixes
   - Known issues
   - Installation instructions

## Security Considerations

- **Never include API keys** in the executable or distribution package
- The executable bundles all code - keep it up to date with security patches
- Consider code signing (Windows) or notarization (macOS) for better trust
- Document that users should download only from official sources

## Continuous Integration

For automated builds, you can integrate PyInstaller into your CI/CD pipeline:

### GitHub Actions Example

```yaml
name: Build Executable
on: [push, release]

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [windows-latest, ubuntu-latest, macos-latest]
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pyinstaller
    
    - name: Build executable
      run: pyinstaller --clean --noconfirm mtk_log_inspector.spec
    
    - name: Upload artifact
      uses: actions/upload-artifact@v2
      with:
        name: executable-${{ matrix.os }}
        path: dist/
```

## Additional Resources

- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [PyInstaller Spec Files](https://pyinstaller.org/en/stable/spec-files.html)
- [tkinter Packaging Guide](https://tkdocs.com/tutorial/install.html)

## Support

For issues with building or distributing executables, please open an issue on the GitHub repository.
