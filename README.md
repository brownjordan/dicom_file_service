## dicom_file_service

#### Description

A microservice that provides the following functionality:

- accept and store an uploaded DICOM file
- extract and return any DICOM header attribute based on a DICOM Tag as a query parameter
- convert the file into a PNG for browser viewing

#### Assumptions

- authentication and SSL termination will take place in an API Gateway layer in front of this microservice
- a file backup mechanism is in place (if the host machine dies, all files will be lost)

#### Notes

- This will not be easy to horizontally scale, as we'd have to keep track of which files are on which service instances in a proxy layer.
- Generally, I'd handle this using direct client upload to an object store using a pre-signed URL, and the microservice would just be responsible for generating pre-signed URLs for upload and download, as well as storing the file location to a DB.
- pngs are generated on-demand. If we know we're DEFINITELY going to need a png representation, it would be better to start a background task to perform the conversion when the DICOM is initially uploaded
- With more time I would:
  - add gunicorn to serve the Flask app (a production wsgi server). better performance, more tuning options (gevent, threads, etc)
  - add a database to store file paths/URLs (raw, processed) and associated metadata, in preparation for:
  - move files to an object store (either upload directly from client with presigned urls, or from the server -> could offload to background task)

### Deploy with docker compose

```bash
$ docker compose up -d
```

### Usage

1. Upload a DICOM file to the service:

```bash
$ curl -X POST -F "file=@IM000001" http://localhost:80/dicom-image
```

This will return JSON containing the generated file ID:

```
{
    "file_id": "<FILE_ID>"
}
```

2. Retrieve the uploaded DICOM file (use the file id returned from the upload API call):

```bash
$ curl "http://localhost:80/dicom-image/<FILE_ID>"
```

3. Retrieve DICOM header attribute for the file (use the file id returned from the upload API call):

```bash
$ curl "http://localhost:80/dicom-image/<FILE_ID>?dicom_tag=(0010,0010)"
```

4. Retrieve a PNG representation of the file (use the file id returned from the upload API call):

```bash
$ curl "http://localhost:80/dicom-image/<FILE_ID>/png"
```

### Testing

There are some very basic integration tests which can be run with docker:

```bash
$ docker-compose --profile testing up
```