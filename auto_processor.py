import threading
import time
from typing import Callable, Optional
from supabase import Client

class AutoProcessor:
    def __init__(self, supabase: Client, process_task_fn: Callable, log_action_fn: Callable):
        self.supabase = supabase
        self.process_task = process_task_fn
        self.log_action = log_action_fn
        self.auto_processing = False
        self.auto_process_thread: Optional[threading.Thread] = None
        self.tasks_processed = set()
        self.currently_processing = False

    def start(self):
        """Start automatic task processing"""
        self.auto_processing = True
        if not self.auto_process_thread or not self.auto_process_thread.is_alive():
            self.auto_process_thread = threading.Thread(target=self._process_loop, daemon=True)
            self.auto_process_thread.start()

    def stop(self):
        """Stop automatic task processing"""
        self.auto_processing = False
        self.auto_process_thread = None

    def _process_loop(self):
        """Main processing loop for automatic tasks"""
        while self.auto_processing:
            try:
                # Get all pending tasks
                response = self.supabase.table('tasks').select('*').eq('status', 'pending').execute()
                pending_tasks = response.data

                if not pending_tasks:
                    self.log_action("No pending tasks found. Waiting for new tasks...")
                    time.sleep(5)
                    continue

                # Process each pending task
                for task in pending_tasks:
                    if not self.auto_processing:
                        break

                    task_id = task['id']
                    if task_id not in self.tasks_processed and not self.currently_processing:
                        try:
                            self.currently_processing = True
                            self.log_action(f"Processing task: {task['title']}")
                            
                            # Update status to in_progress
                            self.supabase.table('tasks').update({
                                'status': 'in_progress'
                            }).eq('id', task_id).execute()

                            # Process the task
                            self.process_task(task)
                            self.tasks_processed.add(task_id)

                        except Exception as e:
                            self.log_action(f"Error processing task {task_id}: {str(e)}")
                            self.supabase.table('tasks').update({
                                'status': 'failed',
                                'agent_message': f"Error: {str(e)}"
                            }).eq('id', task_id).execute()

                        finally:
                            self.currently_processing = False

                # Small delay to prevent excessive database queries
                time.sleep(2)

            except Exception as e:
                self.log_action(f"Error in processing loop: {str(e)}")
                time.sleep(5)

    @property
    def is_running(self) -> bool:
        """Check if auto-processing is running"""
        return self.auto_processing and (self.auto_process_thread is not None and self.auto_process_thread.is_alive())