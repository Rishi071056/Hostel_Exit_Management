import face_recognition


def generate_face_embedding(image_bytes: bytes):
    image = face_recognition.load_image_file(
        __import__("io").BytesIO(image_bytes)
    )

    face_encodings = face_recognition.face_encodings(image)

    if len(face_encodings) == 0:
        raise ValueError("No face detected in the image")

    if len(face_encodings) > 1:
        raise ValueError(
            "Multiple faces detected. Please upload an image with only one face"
        )

    return face_encodings[0].tolist()


def verify_face(image_bytes: bytes, stored_embedding: list):
    image = face_recognition.load_image_file(
        __import__("io").BytesIO(image_bytes)
    )

    face_encodings = face_recognition.face_encodings(image)

    if len(face_encodings) == 0:
        raise ValueError("No face detected in the image")

    if len(face_encodings) > 1:
        raise ValueError(
            "Multiple faces detected. Please upload an image with only one face"
        )

    current_embedding = face_encodings[0]

    stored_embedding = [
        float(value) for value in stored_embedding
    ]

    match = face_recognition.compare_faces(
        [stored_embedding],
        current_embedding,
        tolerance=0.25
    )

    return match[0]