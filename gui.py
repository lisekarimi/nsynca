"""
Entry point for the GUI application.
"""

from gui.main_window import NotionUpdaterGUI


def main():
    """Run the GUI application."""
    app = NotionUpdaterGUI()
    app.run()


if __name__ == "__main__":
    main()
