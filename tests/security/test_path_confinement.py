import os
import pytest
from pathlib import Path
from unilog.utils import validate_path_safety

def test_sandbox_path_confinement_scenarios(tmp_path) -> None:
    # 1. Setup Sandbox Directories
    sandbox_dir = tmp_path / "sandbox"
    sandbox_dir.mkdir()
    
    safe_file = sandbox_dir / "safe.log"
    safe_file.write_text("safe log file content")
    
    nested_dir = sandbox_dir / "logs"
    nested_dir.mkdir()
    nested_file = nested_dir / "test.log"
    nested_file.write_text("nested log file content")
    
    # Setup Outside Directory
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    unsafe_file = outside_dir / "unsafe.log"
    unsafe_file.write_text("unauthorized file content")
    
    # 2. Enable Sandbox Root Constraint
    os.environ["UNILOG_SANDBOX_ROOT"] = str(sandbox_dir)
    
    try:
        # Scenario A: Valid Sandbox Files (Expected to Pass)
        res_safe = validate_path_safety(str(safe_file))
        assert Path(res_safe).resolve() == safe_file.resolve()
        
        res_nested = validate_path_safety(str(nested_file))
        assert Path(res_nested).resolve() == nested_file.resolve()
        
        # Scenario B: Traversal Attempts (Expected to raise PermissionError)
        traversal_path = str(sandbox_dir) + "/../outside/unsafe.log"
        with pytest.raises(PermissionError) as exc_info:
            validate_path_safety(traversal_path)
        assert "escapes the sandbox root" in str(exc_info.value)
        
        # Scenario C: Absolute Paths Outside Sandbox (Expected to raise PermissionError)
        with pytest.raises(PermissionError) as exc_info:
            validate_path_safety(str(unsafe_file))
        assert "escapes the sandbox root" in str(exc_info.value)
        
        # Scenario D: Windows Path Edge Cases (Expected to raise PermissionError on Sandbox Bypass)
        # Windows drive-letter traversal simulation
        win_style_traversal = "C:\\Windows\\System32\\drivers\\etc\\hosts"
        with pytest.raises(PermissionError) as exc_info:
            validate_path_safety(win_style_traversal)
        assert "escapes the sandbox root" in str(exc_info.value)

        # Scenario E: Symlink Escape Mitigation
        # Create a symlink nested inside the sandbox pointing to the outside directory
        symlink_target = outside_dir
        symlink_path = sandbox_dir / "escapelink"
        
        try:
            # Create symlink: sandbox/escapelink -> outside
            os.symlink(str(symlink_target), str(symlink_path), target_is_directory=True)
            has_symlink_support = True
        except (OSError, NotImplementedError):
            # Fallback for environments/Windows without developer mode symlink permissions
            has_symlink_support = False
            
        if has_symlink_support:
            escaped_file_via_symlink = symlink_path / "unsafe.log"
            # Accessing files resolved through symlink outside sandbox must be blocked
            with pytest.raises(PermissionError) as exc_info:
                validate_path_safety(str(escaped_file_via_symlink))
            assert "escapes the sandbox root" in str(exc_info.value)

    finally:
        # Cleanup environment variables
        os.environ.pop("UNILOG_SANDBOX_ROOT", None)


def test_validate_path_safety_circuit_breaker() -> None:
    # Verify that raw log contents passed as strings (which contain newlines)
    # trigger immediate ValueError before executing any path-exists checking.
    raw_log = "127.0.0.1 - - [14/Jul/2026] \"GET /index.html HTTP/1.1\" 200 45\n"
    with pytest.raises(ValueError) as exc_info:
        validate_path_safety(raw_log)
    assert "Invalid characters in file path" in str(exc_info.value)
