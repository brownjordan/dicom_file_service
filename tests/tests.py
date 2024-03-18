import requests

"""
Very basic integration tests
"""

if __name__ == '__main__':
    VALID_FILENAME = "IM000001"
    INVALID_FILENAME = "astonmartindb12.jpeg"
    BASE_URL = "http://proxy:80/"
    UPLOAD_URL = f"{BASE_URL}dicom-image"
    DETAIL_URL = f"{BASE_URL}dicom-image/"
    
    # test file upload (invalid file)
    files = { 'file': open(INVALID_FILENAME, 'rb') }
    response = requests.post(UPLOAD_URL, files=files)
    assert response.status_code == 400
    
    # test file upload (valid file)
    files = { 'file': open(VALID_FILENAME, 'rb') }
    response = requests.post(UPLOAD_URL, files=files)
    assert response.status_code == 201
    response_json = response.json()
    assert "file_id" in response_json
    
    file_id = response_json["file_id"]

    # test retrieving DICOM file
    response = requests.get(f"{DETAIL_URL}{file_id}")
    assert response.status_code == 200
    
    # test retrieving tag data
    params = {
        "dicom_tag": "(0010,0010)"
    }
    response = requests.get(f"{DETAIL_URL}{file_id}", params=params)
    assert response.status_code == 200
    response_json = response.json()
    assert "attribute" in response_json
    assert "Value" in response_json["attribute"]
    assert len(response_json["attribute"]["Value"]) == 1
    assert "Alphabetic" in response_json["attribute"]["Value"][0]
    assert response_json["attribute"]["Value"][0]["Alphabetic"] == "NAYYAR^HARSH"
    
    # test retrieving PNG
    response = requests.get(f"{DETAIL_URL}{file_id}/png")
    assert response.status_code == 200