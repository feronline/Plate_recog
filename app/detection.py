import cv2
import numpy as np
import onnxruntime as ort


def preprocess_image(image_path, session, input_size=(640, 640)):

    # Görüntüyü yükle
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Görüntü yüklenemedi: {image_path}")

    original_img = img.copy()

    input_shape = session.get_inputs()[0].shape
    print(f"Model giriş şekli: {input_shape}")
    batch_size, channels, height, width = input_shape

    if isinstance(height, str) or isinstance(width, str):
        height = input_size[0]
        width = input_size[1]
    else:
        height = int(height)
        width = int(width)

    h, w = img.shape[:2]

    scale = min(width / w, height / h)

    new_w, new_h = int(w * scale), int(h * scale)

    resized_img = cv2.resize(img, (new_w, new_h))

    padded_img = np.ones((height, width, 3), dtype=np.uint8) * 114
    padded_img[:new_h, :new_w] = resized_img

    padded_img = padded_img[:, :, ::-1].transpose(2, 0, 1)
    padded_img = np.ascontiguousarray(padded_img) / 255.0
    padded_img = padded_img.astype(np.float32)

    return padded_img[np.newaxis, :, :, :], original_img, (scale, new_h, new_w)


def process_output(output, info, original_img_shape, conf_threshold=0.25, iou_threshold=0.45):

    scale, new_h, new_w = info
    original_height, original_width = original_img_shape[:2]

    print(f"Model çıktı şekli: {[o.shape for o in output]}")

    try:
        predictions = output[0]

        if predictions.shape[0] == 1 and predictions.shape[1] == 5 and predictions.shape[2] > 100:
            predictions = np.transpose(predictions, (0, 2, 1))[0]

            boxes = []
            scores = []
            class_ids = []

            for prediction in predictions:
                confidence = prediction[4]

                if confidence >= conf_threshold:
                    x_center, y_center, width, height = prediction[:4]

                    x1 = max(0, int((x_center - width / 2) / scale))
                    y1 = max(0, int((y_center - height / 2) / scale))
                    x2 = min(original_width, int((x_center + width / 2) / scale))
                    y2 = min(original_height, int((y_center + height / 2) / scale))

                    boxes.append([x1, y1, x2, y2])
                    scores.append(float(confidence))
                    class_ids.append(0)

            if boxes:
                indices = cv2.dnn.NMSBoxes(boxes, scores, conf_threshold, iou_threshold)

                result_boxes = []
                result_scores = []
                result_class_ids = []

                for i in indices:
                    if isinstance(i, (list, np.ndarray)):
                        i = i[0]
                    result_boxes.append(boxes[i])
                    result_scores.append(scores[i])
                    result_class_ids.append(class_ids[i])

                return result_boxes, result_scores, result_class_ids

    except Exception as e:
        print(f"Model çıktısı işlenirken hata: {e}")
        return [], [], []


def visualize_detection(image, boxes, scores, class_ids, class_names=None):

    color = (255, 0, 0)  # BGR formatında mavi
    result = image.copy()

    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = box
        cv2.rectangle(result, (x1, y1), (x2, y2), color, 2)

        if class_names and 0 <= class_ids[i] < len(class_names):
            label = f"{class_names[class_ids[i]]}: {scores[i]:.2f}"
        else:
            label = f"Plaka: {scores[i]:.2f}"

        label_size, baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        y1 = max(y1, label_size[1])
        cv2.rectangle(result, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), color, -1)
        cv2.putText(result, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return result


def detect_plates(model_path, image_path):

    try:
        session = ort.InferenceSession(model_path)
    except Exception as e:
        print(f"Model yüklenirken hata: {e}")
        return None, None

    input_name = session.get_inputs()[0].name
    print(f"Model giriş adı: {input_name}")

    try:
        input_data, original_img, scale_info = preprocess_image(image_path, session)
    except Exception as e:
        print(f"Görüntü önişleme hatası: {e}")
        return None, None

    try:
        outputs = session.run(None, {input_name: input_data})
    except Exception as e:
        print(f"Model çıkarım hatası: {e}")
        return None, None

    boxes, scores, class_ids = process_output(outputs, scale_info, original_img.shape)

    print(f"Tespit edilen plaka sayısı: {len(boxes)}")

    if len(boxes) > 0:
        result_img = visualize_detection(original_img, boxes, scores, class_ids)
        return result_img, boxes
    else:
        print("Hiç plaka tespit edilemedi.")
        return original_img, []
