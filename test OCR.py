from flask_cors import CORS
import numpy as np
from flask import Flask, request, jsonify
import cv2
import pytesseract
import re

app = Flask(__name__)
CORS(app)
# Chemin vers l'exécutable Tesseract (à adapter selon votre installation)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


@app.route('/process_image', methods=['POST'])
def process_image():
    try:
        # Lecture de l'image à partir de la requête POST
        image_file = request.files['image']
        image = cv2.imdecode(np.frombuffer(
            image_file.read(), np.uint8), cv2.IMREAD_COLOR)

        if image is not None:
          
            # Conversion de l'image en niveaux de gris
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # Binarisation de l'image
            # 150 est la valeur de seuil. Tous les pixels ayant une valeur inférieure à 150 deviendront noirs.
            # cv2.THRESH_BINARY est le type de seuillage appliqué ici. Dans ce cas, si la valeur du pixel est inférieure à 150, le pixel devient noir (0), sinon il devient blanc (255).
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            output_path = 'binaire_pic.jpg'  # Chemin de sortie pour l'image seuillée

            cv2.imwrite(output_path, thresh)

            # Détection des contours dans l'image seuillée / RETR_EXTERNAL pour détecter les contours extérieurs
            contours, _ = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Dessiner les contours sur l'image originale (pour visualisation)
            # Dessine tous les contours trouvés en vert
            cv2.drawContours(image, contours, -1, (0, 255, 0), 2)

            # Enregistrement de l'image avec les contours dessinés
            output_path_with_contours = 'image_with_contours.jpg'
            cv2.imwrite(output_path_with_contours, image)

            # Extraction du texte en parcourant les contours détectés
            extracted_text = ''
            min_text_width = 50  # Définir une largeur minimale pour considérer le contour comme texte

            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)

                # Récupération de la région d'intérêt (ROI) pour l'extraction de texte
                if w > min_text_width:

                    roi = image[y:y+h, x:x+w]
                # Extraction de texte à partir de la ROI avec Tesseract OCR
                    text = pytesseract.image_to_string(
                        roi, lang='eng')  # Choisir la langue appropriée
                    if text.strip():  # Vérifier si le texte extrait n'est pas vide
                        extracted_text += text + '\n'

            # Votre texte extrait

            # Expression régulière pour rechercher le mot "Total" suivi d'un montant
            # Pattern pour "Total" suivi d'un montant décimal
            total_amount_pattern = r'Total:\s*[\w\s]*=\s*(\d+\.\d+)'
            date_pattern = r'\b\d{2}\.\d{2}\.\s*\d{4}\b'
            # Recherche de correspondances dans le texte extrait
            matches = re.search(total_amount_pattern, extracted_text)
            matches_date = re.search(date_pattern, extracted_text)
            # Si une correspondance est trouvée, le montant est extrait
            if matches:
                # On récupère le montant capturé par les parenthèses dans le pattern
                total_amount = matches.group(1)
                print("Montant total extrait :", total_amount)
            else:
                print("Aucun montant total trouvé dans le texte extrait.")
            if matches_date:
                date = matches_date.group(0)
                print("Date extraite :", date)
            else:
                print("Aucune date trouvée dans le texte extrait.")

            # Affichage du texte extrait
            # print(extracted_text)
            return jsonify({'total': total_amount, 'date': date})

    except Exception as e:
        # Print the exception traceback
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True)
