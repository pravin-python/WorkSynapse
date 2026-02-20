from locust import HttpUser, task, between

class WorkSynapseUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login on start."""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "test@example.com",
            "password": "password123"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task(3)
    def view_projects(self):
        """View projects list."""
        if self.token:
            self.client.get("/api/v1/projects/", headers=self.headers)

    @task(5)
    def view_notes(self):
        """View notes list."""
        if self.token:
            self.client.get("/api/v1/notes/", headers=self.headers)

    @task(1)
    def create_note(self):
        """Create a new note."""
        if self.token:
            self.client.post("/api/v1/notes/", headers=self.headers, json={
                "title": "Load Test Note",
                "content": "Created by Locust"
            })

    @task(2)
    def chat_with_agent(self):
        """Simulate chatting with an agent."""
        if self.token:
            # First list agents to get an ID (assuming endpoint exists)
            # For simplicity, we might skip this or hardcode if we knew IDs.
            # self.client.post(...)
            pass
