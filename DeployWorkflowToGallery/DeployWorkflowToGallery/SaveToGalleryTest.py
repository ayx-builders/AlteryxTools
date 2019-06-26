from SaveToGallery import save_to_gallery


base_url = input("Enter the base URL:")
api_key = input("Enter the API key:")
api_secret = input("Enter the API secret:")
file_name = input("Enter the path to a workflow:")
name = input("Enter a name for the new workflow:")
owner = input("Enter the e-mail address of the workflow owner:")

result = save_to_gallery(base_url, api_key, api_secret, file_name, name, owner)
print(result)
