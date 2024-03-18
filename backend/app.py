import json
import os
import uuid
from pathlib import Path

from flask import Flask, send_file
from flask_restful import Resource, Api, reqparse
import werkzeug

import numpy as np
import png
import pydicom

"""
Microservice that will:
- accept and store an uploaded DICOM file
- extract and return any DICOM header attribute based on a DICOM Tag as a query parameter
- convert the file into a PNG for browser viewing

Assumptions:
- authentication and SSL termination will take place in an API Gateway layer in front of this microservice

Note: 
- Generally, I'd handle this using direct client upload to an object store using a pre-signed URL,
and the microservice would just be responsible for generating pre-signed URLs for upload and download,
as well as storing the file location to a DB.
"""


app = Flask(__name__)
api = Api(app)


class BaseDICOMImage:
    
    BASE_FILE_LOCATION = "files"
    RAW_FILE_LOCATION = Path(BASE_FILE_LOCATION) / Path("raw")
    PROCESSED_FILE_LOCATION = Path(BASE_FILE_LOCATION) / Path("processed")
    
    def raw_filepath(self, filename):
        return self.RAW_FILE_LOCATION / Path(filename)
        
    def processed_filepath(self, filename):
        return self.PROCESSED_FILE_LOCATION / Path(filename)

    def check_raw_file_exists(self, filename):
        if not self.raw_filepath(filename).exists():
            return False
        return True


class DICOMImage(BaseDICOMImage, Resource):
    """
    Handles uploads of DICOM files
    """

    def post(self):
        """
        Accept a file (of any type), store it locally and return the generated file id
        """
        
        # retrieve the file from the request
        parser = reqparse.RequestParser()
        parser.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
        args = parser.parse_args()
        filedata = args['file']
        
        # generate a unique filename (to avoid file naming collisions)
        filename = str(uuid.uuid4())
        filepath = self.raw_filepath(filename)
        filepath.parent.mkdir(exist_ok=True, parents=True)
        # ideally this file would be stored in an object store service instead of locally 
        filedata.save(filepath)
        
        return {'file_id': filename}, 201


class DICOMImageDetail(BaseDICOMImage, Resource):
    """
    Handles retrieving uploaded DICOM files and extracting any specified DICOM header attributes
    """
    
    def get(self, file_id):
        """
        Return the specified DICOM header attribute for the specified file
        """
        
        # first ensure the specified file exists
        if not self.check_raw_file_exists(file_id):
            return {'error': 'The specified file does not exist'}, 404
            
        # check if we're looking up a DICOM header attribute by tag
        parser = reqparse.RequestParser()
        parser.add_argument('dicom_tag', type=str, location='args')
        args = parser.parse_args()
        if "dicom_tag" in args and args["dicom_tag"]:
            # split the tag into separate components (group and element)
            raw_dicom_tag = args["dicom_tag"]
            # remove any enclosing brackets
            raw_dicom_tag = raw_dicom_tag.replace("(", "").replace(")", "").strip()
            dicom_tags = [x.strip() for x in raw_dicom_tag.split(',')]
            if len(dicom_tags) < 2 or not dicom_tags[0] or not dicom_tags[1]:
                return {'error': "The dicom tag parameter must be in the following format: '(0010,0010)'." }, 400
                
            dataset = pydicom.dcmread(self.raw_filepath(file_id))
            try:
                attribute_element = dataset.get(dicom_tags)
                attribute = "{}"
                if attribute_element:
                    attribute = attribute_element.to_json()
            
                return {'attribute': json.loads(attribute) }
            except TypeError as e:
                return {'error': 'Invalid DICOM tag'}, 400
                
        # if we're not looking up any DICOM header attributes, return the raw image
        return send_file(self.raw_filepath(file_id), mimetype='application/dicom')
        
        
class ConvertedDICOMImage(BaseDICOMImage, Resource):
    
    """
    Return a transcoded representation of the specified DICOM file
    """
    
    FORMAT_PNG = "png"
    ALLOWED_FORMATS = [
        FORMAT_PNG
    ]
    
    def get(self, file_id, fileformat):
        # first ensure the specified file exists
        if not self.check_raw_file_exists(file_id):
            return {'error': 'The specified file does not exist'}, 404
        
        # ensure the format is correct
        if fileformat not in self.ALLOWED_FORMATS:
            return {'error': f'Requested file format must be one of: {",".join(self.ALLOWED_FORMATS)}'}
            
        if fileformat == self.FORMAT_PNG:
            # don't generate the PNG if it already exists
            final_image_filepath = self.processed_filepath(file_id + "." + self.FORMAT_PNG)
            if not final_image_filepath.exists():
                # convert the DICOM image to PNG
                dataset = pydicom.dcmread(self.raw_filepath(file_id))
                shape = dataset.pixel_array.shape
                new_image = dataset.pixel_array.astype(float)
                scaled_image = (np.maximum(new_image, 0) / new_image.max()) * 255.0
                scaled_image = np.uint8(scaled_image)
            
                # write the PNG data to disk
                final_image_filepath.parent.mkdir(exist_ok=True, parents=True)
                with open(final_image_filepath, 'wb') as png_file:
                    w = png.Writer(shape[1], shape[0], greyscale=True)
                    w.write(png_file, scaled_image)
        
            # return the image
            return send_file(final_image_filepath, mimetype=f'image/{self.FORMAT_PNG}')
            
        return {}
        

api.add_resource(DICOMImage, '/dicom-image')
api.add_resource(DICOMImageDetail, '/dicom-image/<string:file_id>')
api.add_resource(ConvertedDICOMImage, '/dicom-image/<string:file_id>/<string:fileformat>')


if __name__ == '__main__':
    app.run()