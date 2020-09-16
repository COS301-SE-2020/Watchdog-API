import boto3
import os
import json
import PIL
from PIL import Image
from io import BytesIO
from botocore.client import Config


def get_bounding_boxes(img_name, rekognition):
    response = rekognition.detect_labels(
        Image={
            'S3Object': {
                'Bucket': os.environ['BUCKET'],
                'Name': img_name
            }
        },
        MinConfidence=90
    )
    print("TEMP: Rekognition response: " + str(response))

    for label in response['Labels']:
        if label['Name'] == "Person" and label['Confidence'] > 90:
            bounding_boxes = []
            for instance in label['Instances']:
                bounding_boxes.append(instance)
            bounding_boxes = [b['BoundingBox'] for b in bounding_boxes]
            return bounding_boxes
    return None


def get_meta_data_from_event(event, s3):
    bucket = os.environ['BUCKET']
    record = event['Records'][0]['s3']
    key = record['object']['key']
    metadata = s3.head_object(Bucket=bucket, Key=key)
    metadata = metadata['ResponseMetadata']['HTTPHeaders']
    metadata = {
        'uuid': metadata['x-amz-meta-uuid'],
        'tag': metadata['x-amz-meta-tag'],
        'camera_id': metadata['x-amz-meta-camera_id'],
        'timestamp': metadata['x-amz-meta-timestamp'],
        'token': metadata['x-amz-meta-token']
    }
    return key, metadata


def get_crop_areas(bounding_boxes, img):
    crop_areas = []
    for box in bounding_boxes:
        # xmin = int(box['Left'] * img.size[1])
        # xmax = xmin + int(box['Width'] * img.size[1])
        # ymin = int(box['Top'] * img.size[0])
        # ymax = ymin + int(box['Height'] * img.size[0])

        # get dimensions of faces
        # [left,top, left + width, top + height] width, height = image. size.
        imgWidth, imgHeight = img.size

        left = imgWidth * box['Left']
        top = imgHeight * box['Top']
        width = imgWidth * box['Width']
        height = imgHeight * box['Height']

        crop_areas.append((left, top, left + width, top + height))
    return crop_areas


def to_s3(img, key, crop_areas, s3, metadata):
    # get extension of image
    fn, ext = key.split('/')[1].split('.')
    ext = ext.upper()
    if ext in ['JPG', 'JPEG']:
        ext = 'JPEG'
    elif ext in ['PNG']:
        ext = 'PNG'
    else:
        raise S3ImagesInvalidExtension('Extension is invalid')
    # save bytes in memory
    responses = []
    for i, crop_area in enumerate(crop_areas):
        in_mem_file = BytesIO()
        cropped_image = img.crop(crop_area)
        cropped_image.save(in_mem_file, format=ext)

        image_bytes = in_mem_file.getvalue()
        _fn = f"{os.environ['DESTINATION']}{fn}_{i}.{ext}"
        upload_cropped_image = s3.put_object(
            Bucket=os.environ['BUCKET'],
            Key=_fn,
            Body=image_bytes,
            Metadata=metadata
        )
        resp = {
            "filename": _fn,
            "response": upload_cropped_image['ResponseMetadata']['HTTPStatusCode'],
        }
        responses.append(resp)
    return responses


def remove_s3_object(key, s3):
    response = s3.delete_object(
        Bucket=os.environ['BUCKET'],
        Key=key
    )


def lambda_handler(event, context):
    # define resources
    rekognition = boto3.client('rekognition', region_name=os.environ['REKOGNITION_REGION'])
    s3 = boto3.client('s3', config=Config(signature_version='s3v4'))

    key, metadata = get_meta_data_from_event(event, s3)
    print(f"(1. get S3 key and metadata): key:{key};  metadata:{str(metadata)}")

    bounding_boxes = get_bounding_boxes(key, rekognition)
    if bounding_boxes is not None:
        file_byte_string = s3.get_object(Bucket=os.environ['BUCKET'], Key=key)['Body'].read()
        img = Image.open(BytesIO(file_byte_string))
        print(f"TEMP image dimensions. Width:{img.size[0]} Height:{img.size[1]}")
        crop_areas = get_crop_areas(bounding_boxes, img)
        print(f"(2. crop areas of faces in image): crop areas: {crop_areas}")
        to_s3_responses = to_s3(img, key, crop_areas, s3, metadata)
        print(f"(3. uploaded cropped images to s3 responses): {to_s3_responses}")

    remove_s3_object(key, s3)
    print(f"(4. Delete original image): key:{key}")

    return {
        'statusCode': 200,
        'body': json.dumps('Successfully uploaded cropped images to S3')
    }

