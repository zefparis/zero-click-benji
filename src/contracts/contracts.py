import json
import os

class Contracts:
    def __init__(self, contracts_file):
        self.contracts_file = contracts_file
        self.contracts = self.load_contracts()

    def load_contracts(self):
        try:
            with open(self.contracts_file, 'r') as file:
                contracts = json.load(file)
        except FileNotFoundError:
            contracts = {}
        return contracts

    def save_contracts(self):
        with open(self.contracts_file, 'w') as file:
            json.dump(self.contracts, file, indent=4)

    def add_contract(self, contract_id, contract_info):
        if contract_id in self.contracts:
            raise ValueError("Contract already exists")
        self.contracts[contract_id] = contract_info
        self.save_contracts()

    def remove_contract(self, contract_id):
        if contract_id not in self.contracts:
            raise ValueError("Contract does not exist")
        del self.contracts[contract_id]
        self.save_contracts()

    def update_contract(self, contract_id, contract_info):
        if contract_id not in self.contracts:
            raise ValueError("Contract does not exist")
        self.contracts[contract_id] = contract_info
        self.save_contracts()

    def get_contract(self, contract_id):
        return self.contracts.get(contract_id, None)

    def list_contracts(self):
        return list(self.contracts.keys())

    def upload_document(self, contract_id, document_path):
        if contract_id not in self.contracts:
            raise ValueError("Contract does not exist")
        if not os.path.exists(document_path):
            raise ValueError("Document does not exist")
        with open(document_path, 'rb') as file:
            document_data = file.read()
        self.contracts[contract_id]['document'] = document_data
        self.save_contracts()

    def download_document(self, contract_id, download_path):
        if contract_id not in self.contracts:
            raise ValueError("Contract does not exist")
        document_data = self.contracts[contract_id].get('document', None)
        if document_data is None:
            raise ValueError("No document found for this contract")
        with open(download_path, 'wb') as file:
            file.write(document_data)

    def update_document(self, contract_id, document_path):
        self.upload_document(contract_id, document_path)

    def detect_anomalies(self, data):
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
            print(f"Error detecting anomalies: {e}")
            return []
        if contract_id not in self.contracts:
            raise ValueError("Contract does not exist")
        self.contracts[contract_id] = contract_info
        self.save_contracts()

    def get_contract(self, contract_id):
        return self.contracts.get(contract_id, None)

    def list_contracts(self):
        return list(self.contracts.keys())

    def upload_document(self, contract_id, document_path):
        if contract_id not in self.contracts:
            raise ValueError("Contract does not exist")
        if not os.path.exists(document_path):
            raise ValueError("Document does not exist")
        self.save_contracts()

    def download_document(self, contract_id, download_path):
        if contract_id not in self.contracts:
            raise ValueError("Contract does not exist")
        document_data = self.contracts[contract_id].get('document', None)
        if document_data is None:
            raise ValueError("No document found for this contract")
        with open(download_path, 'wb') as file:
            file.write(document_data)

            for item in data:
                if item['value'] > threshold:
                    anomalies.append(item)
            return anomalies
