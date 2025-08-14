# ===============================================
# FILE: src/test_enhanced.py
# Test script for enhanced components
# ===============================================

#!/usr/bin/env python3
"""
Test script for enhanced B1Clip components
"""
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def test_enhanced_database():
    """Test enhanced database functionality"""
    try:
        from src.core.database import ClipboardDatabase

        # Use temporary database for testing
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = Path(tmp.name)

        db = ClipboardDatabase(db_path)

        # Test text item
        text_id = db.add_text_item(
            content="Test clipboard text content", metadata={"test": True}
        )

        if text_id > 0:
            print("✅ Enhanced database text test passed")
        else:
            print("❌ Enhanced database text test failed")
            return False

        # Test getting items
        items = db.get_items(limit=10)
        if len(items) > 0 and items[0]["id"] == text_id:
            print("✅ Enhanced database retrieval test passed")
        else:
            print("❌ Enhanced database retrieval test failed")
            return False

        # Test search
        search_results = db.search_items("test")
        if len(search_results) > 0:
            print("✅ Enhanced database search test passed")
        else:
            print("❌ Enhanced database search test failed")
            return False

        # Cleanup
        db.close()
        db_path.unlink()

        return True

    except Exception as e:
        print(f"❌ Enhanced database test error: {e}")
        return False


def test_content_manager():
    """Test content manager functionality"""
    try:
        from PySide6.QtCore import QSize
        from PySide6.QtGui import QPixmap

        from src.core.content_manager import ContentManager

        # Use temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            data_dir = Path(tmp_dir)
            content_manager = ContentManager(data_dir)

            # Test text optimization
            text_analysis = content_manager.optimize_text_content(
                "Test text content for analysis"
            )
            if "preview" in text_analysis and "word_count" in text_analysis:
                print("✅ Content manager text optimization test passed")
            else:
                print("❌ Content manager text optimization test failed")
                return False

            # Test image storage (create a simple test pixmap)
            test_pixmap = QPixmap(QSize(100, 100))
            test_pixmap.fill("red")

            image_path, thumbnail_path, image_data, thumbnail_data = (
                content_manager.store_image(test_pixmap)
            )

            if image_path and Path(image_path).exists():
                print("✅ Content manager image storage test passed")
            else:
                print("❌ Content manager image storage test failed")
                return False

        return True

    except Exception as e:
        print(f"❌ Content manager test error: {e}")
        return False


def test_search_engine():
    """Test search engine functionality"""
    try:
        from src.core.database import ClipboardDatabase
        from src.core.search_engine import SearchEngine

        # Use temporary database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = Path(tmp.name)

        db = ClipboardDatabase(db_path)
        search_engine = SearchEngine(db)

        # Add test data
        db.add_text_item("Python programming tutorial", {"test": True})
        db.add_text_item("JavaScript web development", {"test": True})
        db.add_text_item("Database design patterns", {"test": True})

        # Test search
        results = search_engine.search("python")
        if (
            len(results) > 0
            and "python" in results[0].get("search_content", "").lower()
        ):
            print("✅ Search engine basic search test passed")
        else:
            print("❌ Search engine basic search test failed")
            return False

        # Test search suggestions
        suggestions = search_engine.get_search_suggestions("prog")
        if isinstance(suggestions, list):
            print("✅ Search engine suggestions test passed")
        else:
            print("❌ Search engine suggestions test failed")
            return False

        # Cleanup
        db.close()
        db_path.unlink()

        return True

    except Exception as e:
        print(f"❌ Search engine test error: {e}")
        return False


def test_migration_manager():
    """Test migration manager functionality"""
    try:
        from src.core.migration_manager import MigrationManager

        # Create fake old database structure
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as old_tmp:
            old_db_path = Path(old_tmp.name)

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as new_tmp:
            new_db_path = Path(new_tmp.name)
            new_db_path.unlink()  # Remove so migration can create it

        with tempfile.TemporaryDirectory() as tmp_dir:
            data_dir = Path(tmp_dir)

            # Create old database with test data
            import sqlite3

            conn = sqlite3.connect(str(old_db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE clipboard_history (
                    id INTEGER PRIMARY KEY,
                    content_type TEXT,
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_pinned BOOLEAN DEFAULT FALSE,
                    metadata TEXT
                )
            """
            )

            cursor.execute(
                """
                INSERT INTO clipboard_history (content_type, content, is_pinned)
                VALUES ('text', 'Test migration content', 1)
            """
            )

            conn.commit()
            conn.close()

            # Test migration
            migration_manager = MigrationManager(old_db_path, new_db_path, data_dir)

            if migration_manager.needs_migration():
                result = migration_manager.migrate()
                if result and new_db_path.exists():
                    print("✅ Migration manager test passed")
                else:
                    print("❌ Migration manager test failed")
                    return False
            else:
                print("✅ Migration manager test passed (no migration needed)")

        # Cleanup
        old_db_path.unlink()
        if new_db_path.exists():
            new_db_path.unlink()

        return True

    except Exception as e:
        print(f"❌ Migration manager test error: {e}")
        return False


def test_integration():
    """Test integration between components"""
    try:
        from src.core.clipboard_watcher import ClipboardWatcher
        from src.core.content_manager import ContentManager
        from src.core.database import ClipboardDatabase
        from src.utils.config import Config

        # Use temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            data_dir = Path(tmp_dir)

            # Initialize components
            config = Config()
            db = ClipboardDatabase(data_dir / "test.db")
            content_manager = ContentManager(data_dir)

            # Test clipboard watcher initialization
            watcher = ClipboardWatcher(db, content_manager, config)

            if watcher.database and watcher.content_manager:
                print("✅ Component integration test passed")
            else:
                print("❌ Component integration test failed")
                return False

            # Test text processing pipeline
            test_text = "Integration test content with multiple words"
            text_analysis = content_manager.optimize_text_content(test_text)

            item_id = db.add_text_item(test_text, {"integration_test": True})

            if item_id > 0:
                items = db.get_items(limit=1)
                if len(items) > 0 and items[0]["id"] == item_id:
                    print("✅ Text processing pipeline test passed")
                else:
                    print("❌ Text processing pipeline test failed")
                    return False
            else:
                print("❌ Text processing pipeline test failed")
                return False

            db.close()

        return True

    except Exception as e:
        print(f"❌ Integration test error: {e}")
        return False


def main():
    """Run all enhanced component tests"""
    print("🧪 Testing Enhanced B1Clip - Phase 1...")
    print("=" * 50)

    tests = [
        ("Enhanced Database", test_enhanced_database),
        ("Content Manager", test_content_manager),
        ("Search Engine", test_search_engine),
        ("Migration Manager", test_migration_manager),
        ("Component Integration", test_integration),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")

    print(f"\n📊 Phase 1 Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All Phase 1 tests passed! Enhanced architecture is ready.")
        print("\n🚀 Next steps:")
        print("1. Run: python src/main_enhanced.py")
        print("2. Test migration from old database")
        print("3. Verify improved performance")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
