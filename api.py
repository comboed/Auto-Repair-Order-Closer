import requests
import helper

class API:
    def __init__(self, email, password, location_number):
        self.location = None
        self.locations = {1: "newark", 
                          5: "lga", 
                          11: "miami",
                          12: "ft lauderdale"}
        self.session = self.create_session(email, password, location_number)

    def get_headers(self): 
        return {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "original-tenantid": "avisbudgetgroup",
            "clientId": "web",
            "locale": "en_US",
            "program": "DEFAULT",
            "applicationId": "ARC_NA",
            "subApplicationId": "US",
            "productIds": "ARC",
            "flattenedAecProgramsMap": "undefined",
            "oemId": "undefined",
            "Origin": "https://app.tekioncloud.com",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Connection": "keep-alive"
        }

    def create_session(self, email, password, location_number):
        session = requests.Session()
        session.headers = self.get_headers()
        self.login(session, email, password, location_number)
        return session
    
    def set_authentication_data(self, session, data, location_number):
        session.headers.update({
            "tekion-api-token": data["access_token"],
            "roleId": data["rolesResources"][0]["roleResourcePermissions"][0]["roleID"],
            "userId": data["id"],
            "tenantname": data["tenantName"],
            "tenantId": data["rolesResources"][0]["roleResourcePermissions"][0]["tenantId"],
            "original-user-id": data["originalUserId"],
            "original-tenantid": data["originalTenantId"],
            "dealerId": data["dealer"][0]["dealerId"],
            "tek-siteId": str(location_number)
        })
        self.location = self.locations[location_number]

    def login(self, session, email, password, location_number):
        response = session.post("https://app.tekioncloud.com/api/loginservice/p/authenticate/password", json = {
            "email": email,
            "password": password
        })
        if response.status_code != 200:
            print("Failed to login with credentials")
            exit(0)  
        elif location_number not in self.locations.keys():
            print("Unknown service center")
            exit(0) 
        self.set_authentication_data(session, response.json()["data"]["loginData"], location_number)
    
    def lookup_repair_order(self, ro_number):
        response = self.session.post("https://app.tekioncloud.com/api/gss/u/v2/search", json = {
            "entities": [{"entity": "ro", "rows": 300, "filters": []}],
            "searchText": ro_number
        }).json()
        return helper.parse_invoices(response["data"]["entityResponses"][0])
    
    def reopen_invoice(self, invoice_id):
        return self.session.put("https://app.tekioncloud.com/api/service-module/u/ro/" + invoice_id + "/status", json = {
            "reason": "",
            "action": "REOPEN"
        }).status_code in [200, 500]
    
    def append_jobs(self, invoice):
        try:
            response = self.session.post("https://app.tekioncloud.com/api/service-module/u/ro/" + invoice["invoice_id"] + "/job/calculate?roDetailsReq=true", json = [])
            return helper.parse_jobs(invoice, response.json()["data"])
        except Exception as e: # theres an error with this request sometimes, so im only doing this temporarily to see what is the issue
            print(e)
            print(response.text)
    
    def update_job(self, invoice_id, job_id, body):
        return self.session.put("https://app.tekioncloud.com/api/service-module/u/v2/" + invoice_id  + "/job/" + job_id, data = body).status_code == 200

    def send_invoice(self, invoice_id):
        return self.session.post("https://app.tekioncloud.com/api/service-module/u/ro/invoice/v2/" + invoice_id, json = {
            "notifyCustomerBySms": False,
            "notifyCustomerByEmail": False
        }).status_code == 200
    
    def close_repair_order(self, invoice_id):
        return self.session.put("https://app.tekioncloud.com/api/service-module/u/ro/invoice/" + invoice_id + "/status/bulk", json = [{
            "status":"CLOSED",
            "payType":"INTERNAL",
            "closeWithError":"false"
        }]).status_code == 200

    def close_internals(self, invoice_id):
        return self.session.put("https://app.tekioncloud.com/api/service-module/u/ro/invoice/" + invoice_id + "/status", json = {
            "status":"CLOSED",
            "payType":"INTERNAL",
            "closeWithError":"false"
        }).status_code == 200