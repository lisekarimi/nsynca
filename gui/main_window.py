# gui/main_window.py
"""
Main GUI window with buttons and layout.
"""

import customtkinter as ctk
import os
import queue
from datetime import datetime
from dotenv import load_dotenv
from notion_client import Client
from gui.logs_viewer import LogsViewer

# Import from parent directory
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.client.notion_client import NotionWrapper
from src.services.orchestrator import PageUpdaterOrchestrator

# Import from same package
from .update_logger import UpdateLogger
from .update_runner import UpdateRunner
from .results_display import ResultsDisplay
import tomllib


class NotionUpdaterGUI:
    """Main application window."""

    def __init__(self):
        # Load environment
        load_dotenv()

        # Get version from pyproject.toml
        pyproject_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "pyproject.toml"
        )

        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")
        except tomllib.TOMLDecodeError as e:
            raise ValueError(f"Invalid TOML format in pyproject.toml: {e}")

        # Extract version - raise error if not found
        try:
            version = data["project"]["version"]
        except KeyError as e:
            raise KeyError(f"Version not found in pyproject.toml. Missing key: {e}")

        if not version:
            raise ValueError("Version is empty in pyproject.toml")

        # Set up window
        self.root = ctk.CTk()
        self.root.title(f"Nsynca - v{version}")
        self.root.geometry("900x700")

        # Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Initialize components
        self.orchestrator = None
        self.logger = UpdateLogger()
        self.update_queue = queue.Queue()
        self.runner = None
        self.current_update_type = None

        # Create GUI
        self.create_widgets()

        # Initialize orchestrator
        self.check_and_init()

    def check_and_init(self):
        """Check config and initialize orchestrator."""
        notion_token = os.getenv("NOTION_API_KEY")
        deployments_db_id = os.getenv("DEPLOYMENTS_DB_ID")
        tasks_db_id = os.getenv("TASKS_DB_ID")
        services_db_id = os.getenv("SERVICES_DB_ID")

        if all([notion_token, deployments_db_id, tasks_db_id]):
            try:
                notion_client = Client(auth=notion_token)
                notion_wrapper = NotionWrapper(notion_client)

                # Patch wrapper to track updates
                self._patch_notion_wrapper(notion_wrapper)

                config = {
                    "deployments_db_id": deployments_db_id,
                    "tasks_db_id": tasks_db_id,
                    "services_db_id": services_db_id,
                }

                self.orchestrator = PageUpdaterOrchestrator(notion_wrapper, config)
                self.runner = UpdateRunner(self.orchestrator, self.update_queue)

                self.status_label.configure(text="✓ Ready", text_color="green")
                self.enable_buttons()
                if not services_db_id:
                    self.btn_services.configure(state="disabled")
            except Exception as e:
                self.status_label.configure(
                    text=f"✗ Init Error: {str(e)}", text_color="red"
                )
        else:
            self.status_label.configure(
                text="✗ Missing environment variables", text_color="red"
            )

    def _patch_notion_wrapper(self, notion_wrapper):
        original_update = notion_wrapper.update_page
        services_db_id = os.getenv("SERVICES_DB_ID")

        def tracked_update(page_id, updates):
            result = original_update(page_id, updates)
            page = notion_wrapper.get_page(page_id)
            name = notion_wrapper.extract_title(page)
            db_id = (page.get("parent") or {}).get("database_id")
            if services_db_id and db_id == services_db_id:
                # tell the GUI/logging this is a service update
                self.update_queue.put(("service_update", name, updates))
            else:
                # default to project updates (deployments/tasks)
                self.update_queue.put(("project_update", name, updates))
            return result

        notion_wrapper.update_page = tracked_update

    def create_widgets(self):
        """Create all GUI elements."""
        # Header
        self._create_header()

        # Create tab view
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)

        # Create tabs
        self.tab_update = self.tabview.add("Update")
        self.tab_logs = self.tabview.add("Logs")

        # Update tab content
        self._create_update_tab_content()

        # Logs tab content
        self.logs_viewer = LogsViewer(self.tab_logs)

        # Footer
        self._create_footer()

    def _create_update_tab_content(self):
        """Create content for update tab."""
        # Buttons
        buttons_frame = ctk.CTkFrame(self.tab_update)
        buttons_frame.pack(fill="x", pady=10)

        self.btn_all = ctk.CTkButton(
            buttons_frame,
            text="Update All",
            command=lambda: self.run_update("all"),
            width=180,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            state="disabled",
        )
        self.btn_all.pack(side="left", padx=10, pady=20)

        self.btn_deployments = ctk.CTkButton(
            buttons_frame,
            text="Deployments Only",
            command=lambda: self.run_update("deployment"),
            width=180,
            height=50,
            font=ctk.CTkFont(size=16),
            state="disabled",
        )
        self.btn_deployments.pack(side="left", padx=10, pady=20)

        self.btn_tasks = ctk.CTkButton(
            buttons_frame,
            text="Tasks Only",
            command=lambda: self.run_update("task"),
            width=180,
            height=50,
            font=ctk.CTkFont(size=16),
            state="disabled",
        )
        self.btn_tasks.pack(side="left", padx=10, pady=20)

        self.btn_services = ctk.CTkButton(
            buttons_frame,
            text="Services Only",
            command=lambda: self.run_update("service"),
            width=180,
            height=50,
            font=ctk.CTkFont(size=16),
            state="disabled",
        )
        self.btn_services.pack(side="left", padx=10, pady=20)

        # Status section
        status_frame = ctk.CTkFrame(self.tab_update)
        status_frame.pack(fill="x", pady=10)

        self.update_status_label = ctk.CTkLabel(
            status_frame, text="Ready to update", font=ctk.CTkFont(size=14)
        )
        self.update_status_label.pack(pady=10)

        # Results display
        self.results_display = ResultsDisplay(self.tab_update)

    def _create_header(self):
        """Create header section."""
        header_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title = ctk.CTkLabel(
            header_frame,
            text="Nsynca - Notion API Updater",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        title.pack(side="left")

        self.status_label = ctk.CTkLabel(
            header_frame, text="Checking...", font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="right", padx=20)

    def _create_footer(self):
        """Create footer section."""
        self.footer_label = ctk.CTkLabel(
            self.root, text="No updates yet", font=ctk.CTkFont(size=14)
        )
        self.footer_label.pack(pady=(0, 10))

    def enable_buttons(self):
        """Enable all buttons."""
        self.btn_all.configure(state="normal")
        self.btn_deployments.configure(state="normal")
        self.btn_tasks.configure(state="normal")
        self.btn_services.configure(state="normal")

    def disable_buttons(self):
        """Disable all buttons."""
        self.btn_all.configure(state="disabled")
        self.btn_deployments.configure(state="disabled")
        self.btn_tasks.configure(state="disabled")
        self.btn_services.configure(state="disabled")

    def run_update(self, update_type: str):
        """Start an update run."""
        # Clear results
        self.results_display.clear()

        # Store current update type
        self.current_update_type = update_type

        # Set simple status message
        if update_type == "all":
            self.update_status_label.configure(
                text="Updating all in progress...", text_color="yellow"
            )
        elif update_type == "deployment":
            self.update_status_label.configure(
                text="Updating deployments in progress...", text_color="yellow"
            )
        elif update_type == "task":
            self.update_status_label.configure(
                text="Updating tasks in progress...", text_color="yellow"
            )
        elif update_type == "service":
            self.update_status_label.configure(
                text="Updating services in progress...", text_color="yellow"
            )

        # Disable buttons
        self.disable_buttons()

        # Clear queue
        while not self.update_queue.empty():
            self.update_queue.get()

        # Start logging
        self.logger.start_run(update_type)

        # Run update
        self.runner.run_update(update_type)

        # Start monitoring
        self.monitor_progress()

    def monitor_progress(self):
        """Monitor progress from queue."""
        try:
            while True:
                msg = self.update_queue.get_nowait()

                if msg[0] == "status":
                    # Just keep the running status
                    pass

                elif msg[0] == "project_update":
                    # Track the project update
                    _, project_name, updates = msg
                    self.logger.add_project_update(project_name, updates)

                elif msg[0] == "service_update":
                    # Track the service update
                    _, service_name, updates = msg
                    self.logger.add_service_update(service_name, updates)

                elif msg[0] == "complete":
                    if msg[1] == "success":
                        # Finish logging with success
                        run_data = self.logger.finish_run(success=True)

                        # Show results
                        self.results_display.show_results(run_data)
                        self.update_status_label.configure(
                            text="✓ Update completed successfully!", text_color="green"
                        )

                        projects_cnt = len(run_data.get("projects_updated", {}))
                        services_cnt = len(run_data.get("services_updated", {}))

                        # Update footer
                        self.footer_label.configure(
                            text=f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - "
                            f"{projects_cnt} projects updated - "
                            f"{services_cnt} services updated - "
                            f"Status: {run_data['status']}"
                        )
                    else:
                        # Finish logging with failure
                        run_data = self.logger.finish_run(success=False)
                        error_msg = msg[1].replace("error: ", "")
                        self.update_status_label.configure(
                            text=f"✗ Update failed: {error_msg}", text_color="red"
                        )

                        # Update footer
                        self.footer_label.configure(
                            text=f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - "
                            f"Status: failed"
                        )

                    self.enable_buttons()
                    return

        except queue.Empty:
            pass

        # Continue monitoring
        self.root.after(100, self.monitor_progress)

    def run(self):
        """Start the application."""
        self.root.mainloop()
