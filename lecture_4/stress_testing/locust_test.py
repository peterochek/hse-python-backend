from locust import HttpUser, task, between
import random


class ShopApiUser(HttpUser):
    wait_time = between(1, 3)  # Simulates user think time between requests

    @task(2)
    def get_items(self):
        self.client.get("/item")

    @task(1)
    def create_and_manage_item(self):
        # Create a new item
        item_data = {
            "name": f"Item {random.randint(1, 100000)}",
            "price": round(random.uniform(10.0, 500.0), 2),
        }
        response = self.client.post("/item", json=item_data)
        if response.status_code == 201:
            item_id = response.json()["id"]

            # Get the created item
            self.client.get(f"/item/{item_id}")

            # Update the item
            update_data = {
                "name": f"Updated Item {item_id}",
                "price": round(random.uniform(10.0, 500.0), 2),
            }
            self.client.put(f"/item/{item_id}", json=update_data)

            # Patch the item
            patch_data = {"price": round(random.uniform(10.0, 500.0), 2)}
            self.client.patch(f"/item/{item_id}", json=patch_data)

            # Delete the item
            self.client.delete(f"/item/{item_id}")

    @task(1)
    def create_and_manage_cart(self):
        # Create a new cart
        response = self.client.post("/cart")
        if response.status_code == 201:
            cart_id = response.json()["id"]

            # Add items to the cart
            for _ in range(random.randint(1, 5)):
                item_id = random.randint(1, 100)
                self.client.post(f"/cart/{cart_id}/add/{item_id}")

            # Get the cart
            self.client.get(f"/cart/{cart_id}")

    @task(1)
    def get_carts(self):
        self.client.get("/cart")

    @task(1)
    def get_specific_item(self):
        item_id = random.randint(1, 100)
        self.client.get(f"/item/{item_id}")
