import json

def parse_invoices(json):
    if json.get("count", 0) > 0:
        invoices = {}
        for i, value in enumerate(json["hits"]):
            invoices[i] = {"invoice_id": value["id"], "jobs": {}}
        return invoices

def parse_jobs(invoice, data):
    for i, value in enumerate(data["jobLines"]):
        try:
            job = value["job"]
            if job["status"] == "COMPLETED":
                operation = value["operationLines"][0]
                story = job["operations"][0].get("storyLines", None)
                cause = job.get("causes", None)
                part = operation["operation"]["partLineV2s"]

                invoice["jobs"][i] = {
                    "jobId": value["jobId"],
                    "operationId": operation["operationId"], 
                    "opcode": operation["operation"]["opcode"],
                    "cause": cause[0]["causeText"] if cause else "",
                    "story": story[0]["text"] if story else "",
                    "payType": job["payType"],
                    "mileage": int(data["repairOrder"]["additionalDetail"]["vehicleInfo"]["mileageIn"]),
                    "part": part,
                    "brand": data["repairOrder"]["additionalDetail"]["vehicleInfo"]["make"].lower(),
                    "description": operation["operation"]["opcodeDescription"],
                    "serviceTypeId": operation["operation"]["serviceTypeId"],
                }
        except Exception as error:
            print("EXCEPTION:" + error)
            pass

def create_update_body(job, opcodes):
    try:
        opcode, cause, story, service_type_id = job["opcode"], job["cause"], job["story"], job["serviceTypeId"]
        data = opcodes[opcode].copy() # i forgot dictionaries are mutable
        
        if job["payType"] == "WARRANTY":
            print("Warranty pay type detected")
            return "WARRANTY"
        elif service_type_id not in ["645a4c49e222da385998c9dc", "645a4bd18e090d72d4b17c58", "645a4c56e222da385998c9de", "6480fc256ae36f647f292e4c"]:
            print("Warranty service type detected")
            return
        
        if cause or story:
            if opcode in ["RT1", "RT2", "RT3", "RT4"]:
                keywords = ["nail", "impact", "damage"]
                if service_type_id in ["645a4c56e222da385998c9de", "6480fc256ae36f647f292e4c"]:
                    data["serviceTypeId"] = service_type_id
                elif any(keyword in cause for keyword in keywords) or any(keyword in story for keyword in keywords):
                    data["serviceTypeId"] = "645a4c49e222da385998c9dc"
                else:
                    data["serviceTypeId"] = "645a4bd18e090d72d4b17c58"
   
            elif opcode in ["T", "TIRE"]: # attempt to do tires
                keywords = {"repaired", "fixed", "fix", "patch", "patched", "patching"}
                if any(keyword in story for keyword in keywords) or any(keyword in cause for keyword in keywords):
                    return
                
            # special opcodes
            elif opcode in ["BODY", "IP"]:
                keywords = {"malfunction", "failure", "failed", "fail", "internal", "internal failure"}
                if (any(keyword in story for keyword in keywords) or any(keyword in cause for keyword in keywords)) or job["part"]:
                    print("Warranty job detected (BODY/IP)")
                    return
                elif "damage" in story or "damage" in cause:
                    data["serviceTypeId"] = "645a4c49e222da385998c9dc"
                else:
                    data["serviceTypeId"] = service_type_id
                
            elif opcode in ["B", "BATTERY"]:
                brand = job["brand"]
                mileage = job["mileage"]
                if (brand in ["toyota", "nissan"] and mileage < 36000) or (brand in ["chrysler", "ford", "kia"] and mileage < 65000):
                    print("Warranty job detected (BATTERY)")
                    return
                data["serviceTypeId"] = service_type_id
                
            elif opcode == "CEL":
                keywords = {"malfunction", "failure", "failed", "fail", "internal", "internal failure"}
                if (any(keyword in story for keyword in keywords) or any(keyword in cause for keyword in keywords) or job["part"]):
                    print("Warranty job detected (CEL)")
                    return
                data["serviceTypeId"] = service_type_id

            elif (service_type_id in ["645a4c56e222da385998c9de", "6480fc256ae36f647f292e4c"]):
                data["serviceTypeId"] = service_type_id

        return dump_update_body(job, data)
        
    except KeyError:
        if job["opcode"] in ["MPVI", "UBPREP", "VOID" "NWP"]:
            return "SKIP"
        print("Unknown opcode: {}".format(job["opcode"]))

def dump_update_body(job, data):
    return json.dumps({
        "jobUpdateRequest": {
            "id": job["jobId"],
            "totalLaborTimeInSeconds": data["laborTimeInSeconds"],
            "payType": "INTERNAL",
            "totalLabormAount": {
                "amount": data["laborAmount"],
                "currency": "USD"
            },
            "totalBillingTimeInSeconds": data["laborTimeInSeconds"],
            "concern": data["description"],
            "updatedOperations": [
                {
                    "id": job["operationId"],
                    "payType": "INTERNAL",
                    "opcode": data["opcode"],
                    "opcodeDescription": data["description"],
                    "serviceTypeId": data["serviceTypeId"],
                    "serviceTypeIds": [data["serviceTypeId"]],
                    "laborTimeInSeconds": data["laborTimeInSeconds"],
                    "estimatedTimeInSeconds": data["laborTimeInSeconds"],
                    "laborRateType": "HOURLY",
                    "laborRateId": data["laborRateId"],
                    "laborRateVersionId": None,
                    "billingTimeInSeconds": data["laborTimeInSeconds"],
                    "billingRate": data["billingRate"],
                    "editableFields": [
                        "DESCRIPTION",
                        "LABOR_HOUR",
                        "LABOR_RATE",
                        "LABOR_PRICE",
                        "BILL_RATE"
                    ],
                    "canOverride": True,
                    "laborAmount": {
                        "amount": data["laborAmount"],
                        "currency": "USD"
                    },
                    "costCenterSplitType": "PERCENT",
                    "costCenters": [
                        {
                            "costCenter": data["costCenter"],
                            "value": 100
                        }
                    ],
                    "addedStoryLines": [
                        {
                            "operationId": job["operationId"],
                            "text": data["description"]
                        }
                    ]
                }
            ]
        },
        "entityType": "RO"
    })
