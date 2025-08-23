from locust import HttpUser, task

class WebsiteUser(HttpUser):
    @task
    def load_home(self):
        self.client.get("/")

    # @task
    # def login(self):
    #     self.client.post("/login", data={"username": "test", "password": "123"})
