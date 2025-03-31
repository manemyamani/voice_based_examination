import requests
import json

MATHPIX_API_KEY = "your_api_key_here"

def image_to_mathml(image_path):
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    
    headers = {
        "app_id": "your_app_id",
        "app_key": MATHPIX_API_KEY,
        "Content-type": "application/json"
    }
    
    data = {
        "src": f"data:image/png;base64,{image_data}",
        "formats": ["mathml"]
    }
    
    response = requests.post("https://api.mathpix.com/v3/text", headers=headers, json=data)
    
    result = response.json()
    return result.get("mathml", "")

mathml_output = image_to_mathml("example_math_image.png")
print(mathml_output)
