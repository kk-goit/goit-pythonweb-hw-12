import cloudinary
import cloudinary.uploader

from src.conf.config import settings


class UploadFileService:
    def __init__(self):
        """
        Initialize the UploadFileService with Cloudinary configuration.

        This constructor sets up the Cloudinary configuration using the
        Cloudinary name, API key, and API secret from the settings file.

        Attributes:
            cloud_name (str): The Cloudinary cloud name.
            api_key (str): The Cloudinary API key.
            api_secret (str): The Cloudinary API secret.
        """
        self.cloud_name = settings.CLOUDINARY_NAME
        self.api_key = settings.CLOUDINARY_API_KEY
        self.api_secret = settings.CLOUDINARY_API_SECRET
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    @staticmethod
    def upload_file(file, username) -> str:
        """
        Upload a file to Cloudinary and return the URL of the uploaded image.

        Args:
            file (UploadFile): The file object to be uploaded.
            username (str): The username used to construct the public ID for the file.

        Returns:
            str: The URL of the uploaded image with specified transformations (width, height, crop).

        Note:
            The image is uploaded with a public ID in the format 'RestApp/{username}' and
            is configured to overwrite any existing image with the same ID.
        """
        public_id = f"RestApp/{username}"
        r = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
        src_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
        return src_url
