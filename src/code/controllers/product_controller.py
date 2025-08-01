import logging
from typing import Dict, Any, Optional, List
from src.services.product_service import ProductService

class ProductController:
    def __init__(self, product_service: ProductService):
        self.product_service = product_service

    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        return self.product_service.get_product(product_id)

    def create_product(self, name: str, description: str, price: float, stock: int) -> Optional[int]:
        return self.product_service.create_product(name, description, price, stock)

    def update_product(self, product_id: int, name: Optional[str] = None, description: Optional[str] = None, price: Optional[float] = None, stock: Optional[int] = None) -> bool:
        return self.product_service.update_product(product_id, name, description, price, stock)

    def delete_product(self, product_id: int) -> bool:
        return self.product_service.delete_product(product_id)

    def list_products(self) -> List[Dict[str, Any]]:
        return self.product_service.list_products()

    def detect_anomalies(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Efficient algorithm for anomaly detection.
        """
        try:
            anomalies = []
            threshold = 0.05
            for item in data:
                if item['value'] > threshold:
                    anomalies.append(item)
            return anomalies
        except Exception as e:
            logging.error(f"Error detecting anomalies: {e}")
            return []

    def manage_product_tasks(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manage new product management tasks.
        """
        try:
            task_type = task_data.get("task_type")
            if task_type == "add_product":
                product_info = task_data.get("product_info", {})
                product_id = self.create_product(**product_info)
                return {"status": "success", "product_id": product_id}
            elif task_type == "update_product":
                product_id = task_data.get("product_id")
                product_info = task_data.get("product_info", {})
                success = self.update_product(product_id, **product_info)
                return {"status": "success" if success else "failure"}
            elif task_type == "delete_product":
                product_id = task_data.get("product_id")
                success = self.delete_product(product_id)
                return {"status": "success" if success else "failure"}
            else:
                return {"status": "error", "message": "Invalid task type"}
        except Exception as e:
            logging.error(f"Error managing product tasks: {e}")
            return {"status": "error", "message": str(e)}
