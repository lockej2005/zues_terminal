import pyimgur

IMGUR_CLIENT_ID = "38ec9dc33b07bd7"  # Replace with your Imgur Client ID

def upload_to_imgur(image_path):
    """Uploads an image to Imgur and returns the public URL."""
    im = pyimgur.Imgur(IMGUR_CLIENT_ID)
    uploaded_image = im.upload_image(image_path, title="Uploaded by ZeusTerminal")
    return uploaded_image.link  # Returns the public URL
