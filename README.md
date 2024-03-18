## dicom_file_service

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