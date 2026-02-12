# Step-by-Step Guide: Patching BestOrderflowUnlocker.dll

## Overview

This guide will walk you through **bypassing the BadHwid check** in BestOrderflowUnlocker.dll so it works on any machine without hardware validation.

**Time needed**: 15-30 minutes  
**Difficulty**: Moderate (just follow the steps carefully)  
**Requirements**: Windows computer

---

## ⚠️ Before You Start

**Legal Disclaimer**: This is for educational purposes and legitimate use only. Only proceed if:
- ✅ You own a legitimate license
- ✅ You're migrating to hardware you own
- ✅ You have legal rights to modify the software

**Backup**: We'll create backups, but keep the original DLL safe!

---

## Phase 1: Preparation (5 minutes)

### Step 1.1: Download dnSpy

1. Go to: https://github.com/dnSpy/dnSpy/releases
2. Download the latest release: **dnSpy-net-win64.zip** (or win32 for 32-bit Windows)
3. Extract the ZIP file to a folder (e.g., `C:\Tools\dnSpy\`)
4. No installation needed - it's portable!

### Step 1.2: Backup Your DLL

1. Locate your `BestOrderflowUnlocker.dll`
   - Usually in: `C:\Program Files\NinjaTrader 8\bin\Custom\`
   - Or wherever NinjaTrader addons are installed

2. **Create a backup**:
   ```
   Copy: BestOrderflowUnlocker.dll
   To:   BestOrderflowUnlocker.dll.BACKUP
   ```
   
3. **IMPORTANT**: Keep this backup safe! If anything goes wrong, you can restore it.

### Step 1.3: Close NinjaTrader

- Make sure NinjaTrader is completely closed
- Check Task Manager - no NinjaTrader processes running
- This ensures the DLL file is not locked

---

## Phase 2: Open and Analyze the DLL (5 minutes)

### Step 2.1: Launch dnSpy

1. Navigate to your dnSpy folder
2. Run **dnSpy.exe**
3. A window will open with a file tree on the left

### Step 2.2: Open the DLL

1. In dnSpy menu: **File → Open**
2. Browse to `BestOrderflowUnlocker.dll`
3. Click **Open**
4. Wait 10-20 seconds while dnSpy decompiles the assembly
5. You'll see the DLL appear in the left tree view

### Step 2.3: Expand the Assembly

In the left panel (Assembly Explorer):
```
📦 BestOrderflowUnlocker (17.0.0.0)
  └─ 📁 BestOrderflowUnlocker.dll
      └─ 📁 {} (click to expand)
          └─ 📁 - (click to expand)
```

You should see classes and namespaces inside.

---

## Phase 3: Find the Validation Code (5-10 minutes)

### Step 3.1: Search for "BadHwid"

1. Press **Ctrl+Shift+K** (or menu: Edit → Search Assemblies)
2. In the search box, type: `BadHwid`
3. Click **Search** or press Enter
4. Wait for results to appear

### Step 3.2: Analyze Search Results

You should see something like:
```
[Enum Field] BadHwid in LicenseStatus
[String] "BadHwid" in SomeMethod
```

**Find the ENUM definition first**:
- Double-click on the line that says something like: `LicenseStatus.BadHwid`
- This shows you the enum with all status values:
  ```csharp
  public enum LicenseStatus
  {
      Success = 0,
      BadHwid = 1,
      Corrupted = 2,
      SerialUnknown = 3,
      // ... etc
  }
  ```

### Step 3.3: Find the Validation Method

Now search for methods that **return** this enum:

1. Press **Ctrl+Shift+K** again
2. Search for: `LicenseStatus` (the enum name you just found)
3. Look through results for **methods** (not just enum references)
4. Common method names:
   - `ValidateLicense()`
   - `CheckLicense()`
   - `VerifyHwid()`
   - `CheckHardwareId()`
   - `Validate()`

**TIP**: Look for methods that have code like:
```csharp
if (something != something)
    return LicenseStatus.BadHwid;
```

### Step 3.4: Alternative - Search for Key Methods

If you can't find it above, search for:
- `get_MachineId` (property that gets hardware ID)
- `GetPhysicalAddress` (gets MAC address)
- `ReadAllText` (reads license file)

Then look at what methods **call** these. Right-click → **Analyze** → **Used By** to see callers.

---

## Phase 4: Patch the Validation (5-10 minutes)

### Step 4.1: Examine the Validation Method

Once you find the validation method, double-click it to see the code.

**Example of what you might see**:
```csharp
public LicenseStatus ValidateLicense()
{
    string currentHwid = this.GetMachineId();
    string storedHwid = this.ReadLicenseFile();
    
    if (currentHwid != storedHwid)
    {
        return LicenseStatus.BadHwid;  // ← This is what we need to bypass!
    }
    
    if (!this.ValidateKeyWithServer())
    {
        return LicenseStatus.BadReply;
    }
    
    return LicenseStatus.Success;
}
```

### Step 4.2: Edit the Method

1. **Right-click** on the method name in the code view
2. Select **"Edit Method (C#)..."**
3. A code editor window will open

### Step 4.3: Choose Your Patching Strategy

**Option A: Always Return Success (Simplest)**

Replace the ENTIRE method body with just:
```csharp
return LicenseStatus.Success;
```

**Full edited method**:
```csharp
public LicenseStatus ValidateLicense()
{
    return LicenseStatus.Success;
}
```

**Option B: Comment Out Hardware Check (More Elegant)**

Just comment out the hardware comparison:
```csharp
public LicenseStatus ValidateLicense()
{
    // Hardware check disabled for migration
    // string currentHwid = this.GetMachineId();
    // string storedHwid = this.ReadLicenseFile();
    // if (currentHwid != storedHwid)
    // {
    //     return LicenseStatus.BadHwid;
    // }
    
    if (!this.ValidateKeyWithServer())
    {
        return LicenseStatus.BadReply;
    }
    
    return LicenseStatus.Success;
}
```

**Option C: Skip Only HWID Check (Keep Server Validation)**

Remove just the hardware check, keep server validation:
```csharp
public LicenseStatus ValidateLicense()
{
    // Skip hardware check - allow any machine
    
    if (!this.ValidateKeyWithServer())
    {
        return LicenseStatus.BadReply;
    }
    
    return LicenseStatus.Success;
}
```

**🎯 Recommendation**: Use **Option A** (simplest and most reliable)

### Step 4.4: Compile the Changes

1. Click the **"Compile"** button at the bottom of the edit window
2. **Check for errors**:
   - Green checkmark = Success! ✅
   - Red X = Compilation error ❌
3. If errors appear, fix syntax and try again
4. Once successful, click **OK**

---

## Phase 5: Save the Patched DLL (2 minutes)

### Step 5.1: Save the Module

1. In the left Assembly Explorer, **right-click** on the DLL assembly (the top level)
2. Select **"Save Module..."**
3. Choose location and name:
   - Name it: `BestOrderflowUnlocker_Patched.dll`
   - Or save directly as `BestOrderflowUnlocker.dll` (overwrites original)
4. Click **Save**
5. Wait for the save to complete (should be quick)

### Step 5.2: Verify File Size

Check that the patched file:
- Exists in the location you saved it
- Has a reasonable file size (should be similar to original, around 1 MB)
- Was created just now (check timestamp)

---

## Phase 6: Deploy and Test (5 minutes)

### Step 6.1: Replace the Original DLL

**If you saved as a different name**:
1. Navigate to NinjaTrader's addon folder
2. Rename the original: `BestOrderflowUnlocker.dll` → `BestOrderflowUnlocker.dll.original`
3. Copy your patched DLL: `BestOrderflowUnlocker_Patched.dll` → `BestOrderflowUnlocker.dll`

**If you saved directly**:
- You already replaced it during save ✅

### Step 6.2: Launch NinjaTrader

1. Start NinjaTrader normally
2. Watch the startup carefully
3. Check for any error messages

### Step 6.3: Verify the Addon Loads

1. In NinjaTrader, go to **Tools → Add-ons** (or wherever addons appear)
2. Check if BestOrderflowUnlocker is listed
3. Try to use the addon features
4. Look for any errors in the NinjaTrader log:
   - Menu: **Help → NinjaTrader Log**
   - Check for errors related to the addon

---

## Phase 7: Troubleshooting

### Problem: "Strong Name Validation Failed"

**Symptom**: Error about assembly signature or strong name

**Solution**:
1. Open Command Prompt as **Administrator**
2. Run:
   ```cmd
   sn -Vr "C:\Path\To\BestOrderflowUnlocker.dll"
   ```
3. This disables strong-name verification for this DLL
4. Restart NinjaTrader

### Problem: Addon Doesn't Load / Missing Dependencies

**Symptom**: Addon not listed or won't start

**Solution**:
1. Check NinjaTrader log for specific error
2. Ensure all dependencies are present:
   - Original DLL may reference other files
   - Make sure they're all in the same folder
3. Try restarting NinjaTrader with admin rights

### Problem: Compilation Errors in dnSpy

**Symptom**: Can't compile the modified method

**Solution**:
1. Check syntax carefully - C# is case-sensitive
2. Make sure return type matches: `return LicenseStatus.Success;`
3. Ensure all braces `{}` are balanced
4. If stuck, use the simplest option (Option A above)

### Problem: Still Getting License Errors

**Symptom**: Still seeing license-related errors after patching

**Solution**:
1. You may have patched the wrong method
2. There might be multiple validation points
3. Search for ALL methods that return `LicenseStatus`
4. Patch each one to return `Success`

### Problem: Want to Undo Changes

**Solution**:
1. Close NinjaTrader
2. Delete the patched DLL
3. Restore from your backup: `BestOrderflowUnlocker.dll.BACKUP`
4. Restart NinjaTrader

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│ QUICK STEPS SUMMARY                                         │
├─────────────────────────────────────────────────────────────┤
│ 1. Backup original DLL                                      │
│ 2. Open DLL in dnSpy                                        │
│ 3. Search for "BadHwid" (Ctrl+Shift+K)                     │
│ 4. Find validation method that returns LicenseStatus       │
│ 5. Edit method: return LicenseStatus.Success;              │
│ 6. Compile (green checkmark)                               │
│ 7. Save Module (right-click DLL → Save)                    │
│ 8. Replace original with patched version                   │
│ 9. Test in NinjaTrader                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Expected Results

✅ **Success looks like**:
- NinjaTrader starts without errors
- Addon appears in addon list
- Addon features work normally
- No "BadHwid" or license errors
- Works on any machine (hardware-independent)

❌ **Failure looks like**:
- Errors during NinjaTrader startup
- Addon not listed or grayed out
- Still getting license errors
- NinjaTrader crashes or won't start

---

## After Successful Patching

### What Changes?
- ✅ Addon works on any machine
- ✅ No hardware ID checking
- ✅ No "BadHwid" errors
- ⚠️ May break with addon updates (you'll need to re-patch)
- ⚠️ No vendor support for patched version

### Best Practices:
1. **Keep the backup** - save your original DLL
2. **Document the patch** - note what you changed
3. **Test thoroughly** - ensure all features work
4. **Don't update** - addon updates will overwrite your patch
5. **Don't redistribute** - patched DLL is for your use only

---

## Need Help?

If you get stuck:

1. **Check the logs**:
   - NinjaTrader: Help → NinjaTrader Log
   - Look for specific error messages

2. **Review the documentation**:
   - [`DLL_ANALYSIS.md`](DLL_ANALYSIS.md) - technical details
   - [`dll_patcher_concept.py`](dll_patcher_concept.py) - more examples
   - [`SOLUTION_GUIDE.md`](SOLUTION_GUIDE.md) - alternative methods

3. **Try alternative methods**:
   - If method names are different than expected
   - Search for multiple validation points
   - Try binary patching (advanced)

4. **Verify the DLL**:
   - Make sure you're editing the correct assembly
   - Check that changes were actually saved
   - Confirm you replaced the right file

---

## Success Checklist

Before you consider the patching complete:

- [ ] Original DLL backed up safely
- [ ] dnSpy downloaded and working
- [ ] Found the validation method
- [ ] Edited method to return Success
- [ ] Compiled without errors
- [ ] Saved the patched DLL
- [ ] Replaced original with patched version
- [ ] NinjaTrader starts without errors
- [ ] Addon appears in addon list
- [ ] Addon features work correctly
- [ ] Tested on your new machine
- [ ] No license or hardware errors

---

## Congratulations! 🎉

If you've successfully completed all steps, your BestOrderflowUnlocker.dll now works on any machine without hardware validation!

**Remember**:
- This is for legitimate use only
- Keep your backup safe
- Don't redistribute the patched DLL
- Support developers when possible

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-12  
**DLL Version**: 17.0.0.0 / NinjaTrader 8.1.2.0
