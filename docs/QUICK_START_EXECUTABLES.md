# Quick Start Guide for Executable Distribution

## For Repository Maintainers

This guide helps you quickly build and distribute executable versions of MTK Log LLM Inspector.

## Automated Release Process (Recommended)

1. **Create a new release on GitHub:**
   ```bash
   # Tag the release
   git tag -a v1.0.0 -m "Release version 1.0.0 with executable support"
   git push origin v1.0.0
   ```

2. **Go to GitHub → Releases → "Draft a new release"**
   - Select the tag you just created (v1.0.0)
   - Fill in release title and description
   - Click "Publish release"

3. **GitHub Actions will automatically:**
   - Build executables for Windows, Linux, and macOS
   - Package them with README files
   - Upload them to the release

4. **Download links will appear as:**
   - `MTK_Log_Inspector_Windows.zip`
   - `MTK_Log_Inspector_Linux.tar.gz`
   - `MTK_Log_Inspector_macOS.tar.gz`

## Manual Build Process

If you need to build locally:

### Windows
```cmd
build_exe.bat
```

### Linux/Mac
```bash
./build_exe.sh
```

The executable will be in `dist/MTK_Log_Inspector.exe` (Windows) or `dist/MTK_Log_Inspector` (Linux/Mac).

## Testing the Executable

Before distributing, test on a clean system:

1. **Windows:** Use a Windows VM without Python
2. **Linux:** Use a fresh Ubuntu/Debian container
3. **macOS:** Use a clean macOS system

Test checklist:
- [ ] Application launches successfully
- [ ] Can configure API key
- [ ] Can browse and select log files
- [ ] Can enter specification document
- [ ] Can start analysis (with test API key)
- [ ] Can view results
- [ ] Can save results to files

## Quick Troubleshooting

**Build fails with "Module not found":**
- Add the module to `hiddenimports` in `mtk_log_inspector.spec`

**Executable is too large (>50MB):**
- Consider excluding unused modules in `excludes` section

**"tkinter not found" on Linux:**
```bash
sudo apt-get install python3-tk
```

**Executable won't run on target system:**
- Check the error message (run with console mode)
- Verify all data files are included
- Check file permissions (Linux/Mac)

## Distribution Checklist

When releasing executables:

- [ ] Test executable on clean system
- [ ] Include EXECUTABLE_README.md
- [ ] Add sample log files (optional)
- [ ] Create release notes
- [ ] Update version number in code if needed
- [ ] Test download links work
- [ ] Announce release

## Version Numbering

Follow semantic versioning:
- **v1.0.0** - Major release
- **v1.1.0** - New features
- **v1.0.1** - Bug fixes

## Support

For questions or issues with the build process, see:
- `docs/building_executables.md` - Comprehensive guide
- GitHub Issues - Report problems
- GitHub Discussions - Ask questions
