#!/usr/bin/env python3
"""
Simple test script for Clipboard Manager
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_imports():
    """Test if all modules can be imported"""
    try:
        # Test imports (these are used implicitly by the test)
        from core.clipboard_watcher import ClipboardWatcher  # noqa: F401
        from core.database import ClipboardDatabase  # noqa: F401
        from core.hotkey_manager import HotkeyManager  # noqa: F401
        from ui.popup_window import PopupWindow  # noqa: F401
        from ui.settings_window import SettingsWindow  # noqa: F401
        from ui.system_tray import SystemTray  # noqa: F401
        from utils.autostart import AutostartManager  # noqa: F401
        from utils.config import Config  # noqa: F401
        from utils.image_utils import ImageUtils  # noqa: F401

        print("✅ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_config():
    """Test configuration loading"""
    try:
        from utils.config import Config

        config = Config()
        print(f"✅ Config loaded: {config.get('max_items', 'default')} max items")
        return True
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False


def test_database():
    """Test database operations"""
    try:
        from core.database import ClipboardDatabase
        from utils.config import Config

        config = Config()
        db = ClipboardDatabase()

        # Test adding an item
        item_id = db.add_item(
            content_type="text",
            content="Test clipboard item",
            preview="Test item",
            metadata={"test": True},
        )

        if item_id > 0:
            print(f"✅ Database test passed: added item {item_id}")
            # Clean up
            db.delete_item(item_id)
            return True
        else:
            print("❌ Database test failed: could not add item")
            return False
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Testing Clipboard Manager...")
    print("=" * 40)

    tests = [
        ("Module Imports", test_imports),
        ("Configuration", test_config),
        ("Database Operations", test_database),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")

    print(f"\n📊 Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed! Application is ready to run.")
        print("Run: python src/main.py")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
