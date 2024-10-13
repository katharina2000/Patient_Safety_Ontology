# Verbindung mit Neo4j und Erstellung Graphen in neo4j

# Docker Instanz starten:
# docker run \
#    --restart always \
#    --publish=7474:7474 --publish=7687:7687 \
#    --env NEO4J_AUTH=neo4j/adminadmin \
#    neo4j:5.19.0

# Im Browser öffnen:
# http://localhost:7474/

# Für die Anmeldung:
# URL: "neo4j://localhost:7687"
# user:"neo4j"
# password:"adminadmin"

import hashlib
import requests
from neo4j import GraphDatabase
import ollama #AI
from transformers import pipeline #für die Übersetzung der Begriffe
import re
from datetime import datetime

# UMLS API Informationen
apikey = "c3504451-61e2-47f4-b9c6-3d736a41768b"
version = "2024AA"
uri = "https://uts-ws.nlm.nih.gov"
search_endpoint = f"/rest/search/{version}"
concept_endpoint = f"/rest/content/{version}/concepts/"
full_search_url = uri + search_endpoint

# Verbindung zur Neo4j-Datenbank
neo4j_uri = "neo4j://localhost:7687"
neo4j_user = "neo4j"
neo4j_password = "adminadmin"

# Wörterbuch für englische und deutsche Begriffe (Knoten)
node_dict = {
    "event": {"ger": "Ereignis"},
    "action": {"ger": "Aktion", "synonyms": ["Process", "Procedure", "Task"]},
    "successful_event": {"ger": "erfolgreiches Ereignis"},
    "success": {"ger": "Erfolg"},
    "incident": {"ger": "Vorfall"},
    "harm": {"ger": "Schaden"},
    "critical_incident": {"ger": "Kritischer Vorfall", "synonyms": ["Near Miss"]},
    "adverse_event": {"ger": "unerwünschtes Ereignis", "synonyms": ["Harmful Incident"]},
    "degree_of_harm": {"ger": "Schadensgrad"},
    "avoidability": {"ger": "Vermeidbarkeit"},
    "avoidable_event": {"ger": "vermeidbares Ereignis"},
    "error": {"ger": "Fehler"},
    "non_avoidable_event": {"ger": "nicht-vermeidbares Ereignis"},
    "detection": {"ger": "Erkennung"},
    "timing": {"ger": "Zeit"},
    "too_early": {"ger": "zu früh"},
    "on_time": {"ger": "rechtzeitig"},
    "too_late": {"ger": "zu spät"},
    "result": {"ger": "Ergebnis"},
    "correct": {"ger": "richtig"},
    "incorrect": {"ger": "falsch"},
    "type": {"ger": "Typ"},
    "clinical_administration": {"ger": "Klinische Verwaltung"},
    "handover": {"ger": "Übergabe"},
    "appointment": {"ger": "Termin"},
    "waiting_list": {"ger": "Warteliste"},
    "referral_consultation": {"ger": "Überweisung/Konsultation"},
    "admission": {"ger": "Aufnahme"},
    "discharge": {"ger": "Entlassung"},
    "transfer_of_care": {"ger": "Überweisung der Pflege"},
    "patient_identification": {"ger": "Patientenidentifikation"},
    "consent": {"ger": "Einwilligung"},
    "task_allocation": {"ger": "Aufgabenzuweisung"},
    "response_to_emergency": {"ger": "Reaktion auf Notfall"},
    "clinical_process_procedure": {"ger": "Klinischer Prozess/Verfahren"},
    "screening_prevention_routine_checkup": {"ger": "Screening/Vorsorge/Routinekontrolle"},
    "diagnosis_assessment": {"ger": "Diagnose/Bewertung"},
    "procedure_treatment_intervention": {"ger": "Verfahren/Behandlung/Intervention"},
    "general_care_management": {"ger": "Allgemeine Pflege/Management"},
    "tests_investigations": {"ger": "Tests/Untersuchungen"},
    "specimens_results": {"ger": "Proben/Ergebnisse"},
    "detention_restraint": {"ger": "Festhalten/Beschränkung"},
    "documentation": {"ger": "Dokumentation"},
    "healthcare_associated_infection": {"ger": "gesundheitsbezogene Infektion"},
    "medication_iv_fluids": {"ger": "Medikation/IV-Flüssigkeiten"},
    "prescribing": {"ger": "Verschreibung"},
    "preparation_dispensing": {"ger": "Zubereitung/Abgabe"},
    "presentation_packaging": {"ger": "Präsentation/Verpackung"},
    "delivery": {"ger": "Lieferung"},
    "administration": {"ger": "Verabreichung"},
    "supply_ordering": {"ger": "Bestellung/Lieferung"},
    "storage": {"ger": "Lagerung"},
    "monitoring": {"ger": "Überwachung"},
    "blood_blood_products": {"ger": "Blut/Blutprodukte"},
    "pre_transfusion_testing": {"ger": "Vortestung der Transfusion"},
    "nutrition": {"ger": "Ernährung"},
    "oxygen_gas_vapour": {"ger": "Sauerstoff/Gas/Dampf"},
    "cylinder_labeling_color_coding_pin_indexing": {"ger": "Zylinderkennzeichnung/Farbkodierung/PIN-Indizierung"},
    "prescription": {"ger": "Rezept"},
    "medical_device_equipment": {"ger": "Medizinisches Gerät/Ausrüstung"},
    "behavior": {"ger": "Verhalten"},
    "patient_accidents": {"ger": "Patientenunfälle"},
    "infrastructure_building_fixtures": {"ger": "Infrastruktur/Gebäude/Einrichtungen"},
    "resources_organizational_management": {"ger": "Ressourcen/Organisatorisches Management"},
    "person": {"ger": "Person"},
    "patient": {"ger": "Patient"},
    "staff": {"ger": "Mitarbeiter"},
    "visitor": {"ger": "Besucher"},
    "care_setting": {"ger": "Pflegeeinrichtung"},
    "hospital": {"ger": "Krankenhaus"},
    "outpatient_clinic": {"ger": "Ambulante Klinik"},
    "patient_process_result": {"ger": "Patientenprozess-Ergebnis"},
    "organizational_outcome": {"ger": "organisatorisches Ergebnis"},
    "health_status": {"ger": "Gesundheitsstatus"},
    "healthy": {"ger": "gesund"},
    "ill": {"ger": "krank"},
    "better": {"ger": "besser"},
    "similar_before": {"ger": "wie vorher"},
    "worse": {"ger": "schlechter"},
    "problem": {"ger": "Problem"},
    "action_not_performed_when_indicated": {"ger": "Aktion nicht wie angegeben durchgeführt"},
    "incomplete_action": {"ger": "Unvollständige Aktion"},
    "inadequate_action": {"ger": "Unzureichende Aktion"},
    "something_not_available": {"ger": "Etwas nicht verfügbar"},
    "wrong_patient": {"ger": "Falscher Patient"},
    "wrong_process_service_treatment_procedure": {"ger": "Falscher Prozess/Dienstleistung/Behandlung/Verfahren"},
    "wrong_body_part_side_site": {"ger": "Falscher Körperteil/Seite/Stelle"},
    "document_missing_or_unavailable": {"ger": "Dokument fehlt oder nicht verfügbar"},
    "delay_in_accessing_document": {"ger": "Verzögerung beim Zugriff auf Dokument"},
    "document_for_wrong_patient": {"ger": "Dokument für falschen Patienten"},
    "unclear_ambiguous_illegible_incomplete_information_in_document": {
        "ger": "Unklare/Mehrdeutige/Unleserliche/Unvollständige Information im Dokument"},
    "wrong_drug": {"ger": "Falsches Medikament"},
    "wrong_dose_strength_or_frequency": {"ger": "Falsche Dosis/Stärke/Häufigkeit"},
    "wrong_formulation_or_presentation": {"ger": "Falsche Formulierung oder Präsentation"},
    "wrong_route": {"ger": "Falsche Route"},
    "wrong_quantity": {"ger": "Falsche Menge"},
    "wrong_dispensing_label_instruction": {"ger": "Falsches Abgabeschild/Anweisung"},
    "contraindication": {"ger": "Gegenanzeige"},
    "wrong_storage": {"ger": "Falsche Lagerung"},
    "omitted_medicine_or_dose": {"ger": "Ausgelassenes Medikament oder Dosis"},
    "expired_medicine": {"ger": "Ablaufendes Medikament"},
    "adverse_drug_reaction": {"ger": "Unerwünschte Arzneimittelreaktion"},
    "wrong_blood_blood_product": {"ger": "Falsches Blut/Blutprodukt"},
    "expired_blood_blood_product": {"ger": "Ablaufendes Blut/Blutprodukt"},
    "adverse_effect": {"ger": "Nebenwirkung"},
    "wrong_diet": {"ger": "Falsche Diät"},
    "wrong_consistency": {"ger": "Falsche Konsistenz"},
    "wrong_gas_vapour": {"ger": "Falsches Gas/Dampf"},
    "wrong_rate_flow_concentration": {"ger": "Falsche Rate/Fluss/Konzentration"},
    "wrong_delivery_mode": {"ger": "Falsche Liefermethode"},
    "failure_to_administer": {"ger": "Fehlende Verabreichung"},
    "contamination": {"ger": "Kontamination"},
    "poor_presentation_packaging": {"ger": "Schlechte Präsentation/Verpackung"},
    "lack_of_availability": {"ger": "Mangelnde Verfügbarkeit"},
    "inappropriate_for_task": {"ger": "Unangemessen für die Aufgabe"},
    "unclean_unsterile": {"ger": "Unsauber/Unsteril"},
    "failure_malfunction": {"ger": "Fehler/Funktionsstörung"},
    "dislodgement_misconnection_removal": {"ger": "Lockerung/Missverbindung/Entfernung"},
    "user_error": {"ger": "Benutzerfehler"},
    "non_existent_inadequate": {"ger": "Nicht vorhanden/Unzureichend"},
    "damaged_faulty_worn": {"ger": "Beschädigt/Fehlerhaft/Abgenutzt"},
    "error_type": {"ger": "Fehlertyp"},
    "medical_error": {"ger": "medizinischer Fehler"},
    "staff_error": {"ger": "Personalfehler"},
    "treatment_error": {"ger": "Behandlungsfehler"},
    "surgical_error": {"ger": "Chirurgischer Fehler"},
    "procedure_error": {"ger": "Verfahrensfehler"},
    "wrong_procedure_error": {"ger": "Fehler bei der Durchführung"},
    "transfusion_error": {"ger": "Transfusionsfehler"},
    "error_of_commission": {"ger": "Fehler der Kommission"},
    "error_of_omission": {"ger": "Fehler der Unterlassung"},
    "infusion_error": {"ger": "Infusionsfehler"},
    "administrative_order_error": {"ger": ""},
    "administration_error": {"ger": "Verwaltungsfehler"},
    "diagnostic_error": {"ger": "Diagnosefehler"},
    "diagnosis_error_death": {},
    "diagnosis_error_complication": {},
    "judgement_error_complication": {},
    "judgement_error_death": {},
    "error_in_judgement": {"ger": "Fehler im Urteil"},
    "therapeutic_error": {"ger": "Therapeutischer Fehler"},
    "duplicate_therapy_error": {"ger": "Doppelte Therapiefehler"},
    "unintentional_therapeutic_error": {"ger": "Unbeabsichtigter therapeutischer Fehler"},
    "radiotherapy_setup_error": {"ger": "Fehler bei der Radiotherapie-Einrichtung"},
    "error_in_medication_process": {"ger": "Fehler im Medikationsprozess"},
    "condition": {"ger": "Zustand"},
    "patient_death_disability": {},
    "patient_death_injury": {},
    "medication_error": {"ger": "Medikationsfehler"},
    "circumstance_leading_to_error": {},
    "application_program_problem": {},
    "labeled_medication_monitoring_error": {},
    "identify_assess_report_error": {},
    "other_product_use_errors": {},
    "unintended_use_error": {},
    "increased_risk_for_error": {},
    "medication_administered_in_error": {},
    "feeding_history_error": {},
    "incorrect_action_error": {},
    "product_temperature_deviation_error": {},
    "wrong_substance_given_error": {},
    "drug_dispensation_issue": {},
    "product_dispensation_errors": {},
    "error_to_dispense_as_written": {},
    "drug_prescribing_error": {},
    "missed_dose_error": {},
    "device_associated_error": {},
    "software_problem_device_error": {},
    "labelled_drug_drug_interaction_error": {},
    "labelled_drug_disease_interaction_error": {},
    "labelled_drug_food_interaction_error": {},
    "labelled_drug_alcohol_interaction_error": {},
    "labelled_drug_genetic_interaction_error": {},
    "intercepted_error_status": {},
    "drug_not_taken_intercepted_error": {},
    "intercepted_medication_error": {},
    "intercepted_product_dispensation_error": {},
    "intercepted_drug_dispensation_error": {},
    "intercepted_product_monitoring_error": {},
    "intercepted_product_administration_error": {},
    "intercepted_drug_administration_error": {},
    "intercepted_product_prescribing_error": {},
    "intercepted_product_selection_error": {},
    "intercepted_drug_prescribing_error": {},
    "intercepted_product_preparation_error": {},
    "intercepted_product_storage_error": {},
    "intercepted_wrong_patient_selected": {},
    "intercepted_wrong_route_administration_selected": {},
    "intercepted_wrong_dosage_form_selected": {},
    "intercepted_wrong_drug_selected": {},
    "intercepted_wrong_drug_product_selected": {},
    "intercepted_wrong_drug_strength_selected": {},
    "never_event_serious_reportable_event": {},
    "prescription_requesting": {},
    "preparation_manufacturing_cooking": {},
    "presentation": {},
    "dispensing_allocation": {},
    "pharmaceutical_error": {"ger": "Pharmafehler"},
    "application_error": {"ger": "Anwendungsfehler"},
    "medication_monitoring_error": {"ger": "Fehler bei der Medikationsüberwachung"},
    "transcription_medication_error": {"ger": "Fehler bei der Transkription der Medikation"},
    "ocular_drug_implant_use_error": {"ger": "Fehler bei der Anwendung von Augenmedikamentenimplantaten"},
    "drug_use_error": {"ger": "Fehler bei der Medikamentenverwendung"},
    "drug_administration_error": {"ger": "Fehler bei der Medikamentenverabreichung"},
    "poisoning_wrong_substance_error": {"ger": "Vergiftung durch falsche Substanz"},
    "drug_dispensation_error": {"ger": "Fehler bei der Arzneimittelabgabe"},
    "drug_titration_error": {"ger": "Fehler bei der Medikamentendosierung"},
    "error_in_prescription": {"ger": "Fehler bei der Verschreibung"},
    "peritoneal_dialysis_prescription_error": {
        "ger": "Fehler bei der Verschreibung für die Peritonealdialyse"},
    "dietary_supplement_prescribing_error": {"ger": "Fehler bei der Verschreibung von Nahrungsergänzungsmitteln"},
    "duplicate_drug_prescription_error": {"ger": "Fehler bei der doppelten Verschreibung von Medikamenten"},
    "drug_route_prescribing_error": {"ger": "Fehler bei der Verschreibung des Medikamentenwegs"},
    "drug_dose_prescribing_error": {"ger": "Fehler bei der Verschreibung der Medikamentendosis"},
    "error_in_dosage_prescription": {"ger": "Fehler in der Dosierung bei der Verschreibung"},
    "drug_schedule_prescribing_error": {"ger": "Fehler bei der Verschreibung des Medikamentenplans"},
    "drug_refill_prescribing_error": {"ger": "Fehler bei der Verschreibung der Medikamentenauffüllung"},
    "drug_administration_duration_prescribing_error": {
        "ger": "Fehler bei der Verschreibung der Verabreichungsdauer von Medikamenten"},
    "drug_monitoring_error": {"ger": "Fehler bei der Medikamentenüberwachung"},
    "drug_storage_error": {"ger": "Fehler bei der Medikamentenlagerung"},
    "drug_preparation_error": {"ger": "Fehler bei der Medikamentenzubereitung"},
    "drug_refill_dispensation_error": {"ger": "Fehler bei der Nachfüllung der Medikamentenabgabe"},
    "incorrect_preparation_error": {
        "ger": "Fehler bei der Vorbereitung, einschließlich falscher Tablettenschneidung"},
    "drug_dose_omission_error": {"ger": "Fehler bei der Dosierungsversäumnis"},
    "dose_calculation_error": {"ger": "Fehler bei der Dosierungsberechnung"},
    "medication_prescribed_in_error": {"ger": "Fehlerhafte Verschreibung von Medikamenten"},
    "medication_dispensed_in_error": {"ger": "Fehlerhafte Abgabe von Medikamenten"},
    "error_reasons": {"ger": "Fehlerursachen"},
    "drug_drug_interaction_error": {"ger": "Fehler bei Wechselwirkungen zwischen Arzneimitteln"},
    "syringe_labeling_error": {"ger": "Fehler bei der Beschriftung von Spritzen"},
    "high_alert_medication_error": {"ger": "Fehler bei hochriskanten Medikamenten"},
    "vaccination_error": {"ger": "Fehler bei der Impfung"},
    "vaccine_preparation_error": {"ger": "Fehler bei der Impfstoffvorbereitung"},
    "circumstances": {"ger": "Umstände", "synonyms": ["Contributing Factors"]},
    "human_factor": {"ger": "Menschlicher Faktor"},
    "negligence": {"ger": "Nachlässigkeit"},
    "missing_knowledge": {"ger": "Fehlendes Wissen"},
    "missing_training": {"ger": "Fehlende Schulung"},
    "environmental_factor": {"ger": "Umweltfaktor"},
    "missing_device": {"ger": "Fehlendes Gerät"},
    "inadequate_room": {"ger": "Unzureichender Raum"},
    "mitigating_factors": {"ger": "Mindernde Faktoren"},
    "ameliorating_actions": {"ger": "Verbesserungsmaßnahmen"},
    "risk": {"ger": "Risiko"},
    "probability_of_error_event": {"ger": "Wahrscheinlichkeit eines Fehlereignisses"},
    "probability_of_harm": {"ger": "Wahrscheinlichkeit von Schaden"},
    "staff_error_no_reach_patient": {"ger": ""},
    "supply_ordering_storage": {"ger": ""}
}

# Erstellung Beziehung-Liste
relationships = [
    ("event", "action", "is_related_to"),
    ("event", "success", "is_related_to"),
    ("success", "successful_event", "is_a"),
    ("success", "incident", "is_related_to"),
    ("incident", "harm", "is_related_to"),
    ("harm", "critical_incident", "is_a"),
    ("harm", "adverse_event", "is_a"),
    ("adverse_event", "degree_of_harm", "has"),
    ("incident", "avoidability", "is_related_to"),
    ("avoidability", "avoidable_event", "is_a"),
    ("avoidable_event", "error", "based_on"),
    ("avoidability", "non_avoidable_event", "is_a"),
    ("incident", "detection", "has"),
    ("action", "timing", "has"),
    ("timing", "too_early", "is"),
    ("timing", "on_time", "is"),
    ("timing", "too_late", "is"),
    ("action", "result", "has"),
    ("result", "correct", "is"),
    ("result", "incorrect", "is"),
    ("action", "type", "has"),
    ("type", "clinical_administration", "is_a"),
    ("clinical_administration", "handover", "is_a"),
    ("clinical_administration", "appointment", "is_a"),
    ("clinical_administration", "waiting_list", "is_a"),
    ("clinical_administration", "referral_consultation", "is_a"),
    ("clinical_administration", "admission", "is_a"),
    ("clinical_administration", "discharge", "is_a"),
    ("clinical_administration", "transfer_of_care", "is_a"),
    ("clinical_administration", "patient_identification", "is_a"),
    ("clinical_administration", "consent", "is_a"),
    ("clinical_administration", "task_allocation", "is_a"),
    ("clinical_administration", "response_to_emergency", "is_a"),
    ("type", "clinical_process_procedure", "is_a"),
    ("clinical_process_procedure", "screening_prevention_routine_checkup", "is_a"),
    ("clinical_process_procedure", "diagnosis_assessment", "is_a"),
    ("clinical_process_procedure", "procedure_treatment_intervention", "is_a"),
    ("clinical_process_procedure", "general_care_management", "is_a"),
    ("clinical_process_procedure", "tests_investigations", "is_a"),
    ("clinical_process_procedure", "specimens_results", "is_a"),
    ("clinical_process_procedure", "detention_restraint", "is_a"),
    ("type", "documentation", "is_a"),
    ("type", "healthcare_associated_infection", "is_a"),
    ("type", "medication_iv_fluids", "is_a"),
    ("medication_iv_fluids", "prescribing", "is_a"),
    ("medication_iv_fluids", "preparation_dispensing", "is_a"),
    ("medication_iv_fluids", "presentation_packaging", "is_a"),
    ("medication_iv_fluids", "delivery", "is_a"),
    ("medication_iv_fluids", "administration", "is_a"),
    ("medication_iv_fluids", "supply_ordering", "is_a"),
    ("medication_iv_fluids", "storage", "is_a"),
    ("medication_iv_fluids", "monitoring", "is_a"),
    ("type", "blood_blood_products", "is_a"),
    ("blood_blood_products", "pre_transfusion_testing", "is_a"),
    ("blood_blood_products", "prescribing", "is_a"),
    ("blood_blood_products", "preparation_dispensing", "is_a"),
    ("blood_blood_products", "delivery", "is_a"),
    ("blood_blood_products", "administration", "is_a"),
    ("blood_blood_products", "storage", "is_a"),
    ("blood_blood_products", "presentation_packaging", "is_a"),
    ("blood_blood_products", "supply_ordering", "is_a"),
    ("type", "nutrition", "is_a"),
    ("nutrition", "prescription_requesting", "is_a"),
    ("nutrition", "preparation_manufacturing_cooking", "is_a"),
    ("nutrition", "supply_ordering", "is_a"),
    ("nutrition", "presentation", "is_a"),
    ("nutrition", "dispensing_allocation", "is_a"),
    ("nutrition", "delivery", "is_a"),
    ("nutrition", "administration", "is_a"),
    ("nutrition", "storage", "is_a"),
    ("type", "oxygen_gas_vapour", "is_a"),
    ("oxygen_gas_vapour", "cylinder_labeling_color_coding_pin_indexing", "is_a"),
    ("oxygen_gas_vapour", "prescription", "is_a"),
    ("oxygen_gas_vapour", "administration", "is_a"),
    ("oxygen_gas_vapour", "delivery", "is_a"),
    ("oxygen_gas_vapour", "supply_ordering_storage", "is_a"),
    ("type", "medical_device_equipment", "is_a"),
    ("type", "behavior", "is_a"),
    ("type", "patient_accidents", "is_a"),
    ("type", "infrastructure_building_fixtures", "is_a"),
    ("type", "resources_organizational_management", "is_a"),
    ("action", "person", "is_related_to"),
    ("person", "patient", "is_a"),
    ("person", "staff", "is_a"),
    ("person", "visitor", "is_a"),
    ("action", "care_setting", "has_location"),
    ("care_setting", "hospital", "is_a"),
    ("care_setting", "outpatient_clinic", "is_a"),
    ("patient", "health_status", "has"),
    ("health_status", "healthy", "is"),
    ("health_status", "ill", "is"),
    ("patient", "patient_process_result", "has"),
    ("result", "patient_process_result", "is"),
    ("result", "organizational_outcome", "is"),
    ("patient_process_result", "better", "is"),
    ("patient_process_result", "similar_before", "is"),
    ("patient_process_result", "worse", "is"),
    ("error", "problem", "based_on"),
    ("problem", "action_not_performed_when_indicated", "is_a"),
    ("problem", "incomplete_action", "is_a"),
    ("problem", "inadequate_action", "is_a"),
    ("problem", "something_not_available", "is_a"),
    ("problem", "wrong_patient", "is_a"),
    ("problem", "wrong_process_service_treatment_procedure", "is_a"),
    ("problem", "wrong_body_part_side_site", "is_a"),
    ("problem", "document_missing_or_unavailable", "is_a"),
    ("problem", "delay_in_accessing_document", "is_a"),
    ("problem", "document_for_wrong_patient", "is_a"),
    ("problem", "unclear_ambiguous_illegible_incomplete_information_in_document", "is_a"),
    ("problem", "wrong_drug", "is_a"),
    ("problem", "wrong_dose_strength_or_frequency", "is_a"),
    ("problem", "wrong_formulation_or_presentation", "is_a"),
    ("problem", "wrong_route", "is_a"),
    ("problem", "wrong_quantity", "is_a"),
    ("problem", "wrong_dispensing_label_instruction", "is_a"),
    ("problem", "contraindication", "is_a"),
    ("problem", "wrong_storage", "is_a"),
    ("problem", "omitted_medicine_or_dose", "is_a"),
    ("problem", "expired_medicine", "is_a"),
    ("problem", "adverse_drug_reaction", "is_a"),
    ("problem", "wrong_blood_blood_product", "is_a"),
    ("problem", "expired_blood_blood_product", "is_a"),
    ("problem", "adverse_effect", "is_a"),
    ("problem", "wrong_diet", "is_a"),
    ("problem", "wrong_consistency", "is_a"),
    ("problem", "wrong_gas_vapour", "is_a"),
    ("problem", "wrong_rate_flow_concentration", "is_a"),
    ("problem", "wrong_delivery_mode", "is_a"),
    ("problem", "failure_to_administer", "is_a"),
    ("problem", "contamination", "is_a"),
    ("problem", "poor_presentation_packaging", "is_a"),
    ("problem", "lack_of_availability", "is_a"),
    ("problem", "inappropriate_for_task", "is_a"),
    ("problem", "unclean_unsterile", "is_a"),
    ("problem", "failure_malfunction", "is_a"),
    ("problem", "dislodgement_misconnection_removal", "is_a"),
    ("problem", "user_error", "is_a"),
    ("problem", "non_existent_inadequate", "is_a"),
    ("problem", "damaged_faulty_worn", "is_a"),
    ("error", "error_type", "is_named_as"),
    ("error_type", "medical_error", "is_a"),
    ("error", "circumstances", "has_cause"),
    ("circumstances", "human_factor", "is_a"),
    ("human_factor", "negligence", "is_a"),
    ("human_factor", "missing_knowledge", "is_a"),
    ("human_factor", "missing_training", "is_a"),
    ("circumstances", "environmental_factor", "is_a"),
    ("environmental_factor", "missing_device", "is_a"),
    ("environmental_factor", "inadequate_room", "is_a"),
    ("error", "mitigating_factors", "has"),
    ("error", "ameliorating_actions", "has"),
    ("error", "risk", "has"),
    ("risk", "probability_of_error_event", "is_a"),
    ("risk", "probability_of_harm", "is_a"),
    ("medical_error", "staff_error", "is_a"),
    ("staff_error", "staff_error_no_reach_patient", "is_a"),
    ("medical_error", "treatment_error", "is_a"),
    ("treatment_error", "surgical_error", "is_a"),
    ("medical_error", "procedure_error", "is_a"),
    ("procedure_error", "wrong_procedure_error", "is_a"),
    ("medical_error", "transfusion_error", "is_a"),
    ("medical_error", "error_of_commission", "is_a"),
    ("medical_error", "error_of_omission", "is_a"),
    ("medical_error", "infusion_error", "is_a"),
    ("medical_error", "administration_error", "is_a"),
    ("administration_error", "administrative_order_error", "is_a"),
    ("medical_error", "diagnostic_error", "is_a"),
    ("diagnostic_error", "diagnosis_error_complication", "is_a"),
    ("diagnostic_error", "diagnosis_error_death", "is_a"),
    ("medical_error", "error_in_judgement", "is_a"),
    ("error_in_judgement", "judgement_error_complication", "is_a"),
    ("error_in_judgement", "judgement_error_death", "is_a"),
    ("medical_error", "therapeutic_error", "is_a"),
    ("therapeutic_error", "duplicate_therapy_error", "is_a"),
    ("therapeutic_error", "unintentional_therapeutic_error", "is_a"),
    ("therapeutic_error", "radiotherapy_setup_error", "is_a"),
    ("medical_error", "error_in_medication_process", "is_a"),
    ("error_in_medication_process", "condition", "has_a"),
    ("condition", "patient_death_disability", "is_a"),
    ("condition", "patient_death_injury", "is_a"),
    ("error_in_medication_process", "pharmaceutical_error", "is_a"),
    ("error_in_medication_process", "medication_error", "is_a"),
    ("medication_error", "circumstance_leading_to_error", "is_a"),
    ("medication_error", "application_error", "is_a"),
    ("application_error", "application_program_problem", "is_a"),
    ("medication_error", "medication_monitoring_error", "is_a"),
    ("medication_monitoring_error", "labeled_medication_monitoring_error", "is_a"),
    ("medication_error", "transcription_medication_error", "is_a"),
    ("medication_error", "ocular_drug_implant_use_error", "is_a"),
    ("medication_error", "identify_assess_report_error", "is_a"),
    ("medication_error", "other_product_use_errors", "is_a"),
    ("medication_error", "incorrect_action_error", "is_a"),
    ("medication_error", "increased_risk_for_error", "is_a"),
    ("error_in_medication_process", "medication_administered_in_error", "is_a"),
    ("error_in_medication_process", "unintended_use_error", "is_a"),
    ("error_in_medication_process", "feeding_history_error", "is_a"),
    ("error_in_medication_process", "product_temperature_deviation_error", "is_a"),
    ("error_in_medication_process", "drug_use_error", "is_a"),
    ("drug_use_error", "wrong_substance_given_error", "is_a"),
    ("error_in_medication_process", "drug_administration_error", "is_a"),
    ("drug_administration_error", "poisoning_wrong_substance_error", "is_a"),
    ("error_in_medication_process", "drug_dispensation_error", "is_a"),
    ("drug_dispensation_error", "drug_dispensation_issue", "is_a"),
    ("drug_dispensation_error", "product_dispensation_errors", "is_a"),
    ("drug_dispensation_error", "error_to_dispense_as_written", "is_a"),
    ("error_in_medication_process", "drug_titration_error", "is_a"),
    ("error_in_medication_process", "error_in_prescription", "is_a"),
    ("error_in_prescription", "peritoneal_dialysis_prescription_error", "is_a"),
    ("error_in_prescription", "drug_prescribing_error", "is_a"),
    ("drug_prescribing_error", "dietary_supplement_prescribing_error", "is_a"),
    ("drug_prescribing_error", "duplicate_drug_prescription_error", "is_a"),
    ("drug_prescribing_error", "drug_route_prescribing_error", "is_a"),
    ("drug_prescribing_error", "drug_dose_prescribing_error", "is_a"),
    ("drug_prescribing_error", "error_in_dosage_prescription", "is_a"),
    ("drug_prescribing_error", "drug_schedule_prescribing_error", "is_a"),
    ("drug_prescribing_error", "drug_refill_prescribing_error", "is_a"),
    ("drug_prescribing_error", "drug_administration_duration_prescribing_error", "is_a"),
    ("error_in_medication_process", "drug_monitoring_error", "is_a"),
    ("error_in_medication_process", "drug_storage_error", "is_a"),
    ("error_in_medication_process", "drug_preparation_error", "is_a"),
    ("drug_preparation_error", "drug_refill_dispensation_error", "is_a"),
    ("drug_preparation_error", "incorrect_preparation_error", "is_a"),
    ("error_in_medication_process", "drug_dose_omission_error", "is_a"),
    ("error_in_medication_process", "missed_dose_error", "is_a"),
    ("error_in_medication_process", "dose_calculation_error", "is_a"),
    ("dose_calculation_error", "device_associated_error", "is_a"),
    ("dose_calculation_error", "software_problem_device_error", "is_a"),
    ("error_in_medication_process", "medication_prescribed_in_error", "is_a"),
    ("error_in_medication_process", "medication_dispensed_in_error", "is_a"),
    ("error_in_medication_process", "error_reasons", "is_a"),
    ("error_reasons", "drug_drug_interaction_error", "is_a"),
    ("error_reasons", "labelled_drug_drug_interaction_error", "is_a"),
    ("error_reasons", "labelled_drug_disease_interaction_error", "is_a"),
    ("error_reasons", "labelled_drug_food_interaction_error", "is_a"),
    ("error_reasons", "labelled_drug_alcohol_interaction_error", "is_a"),
    ("error_reasons", "labelled_drug_genetic_interaction_error", "is_a"),
    ("error_reasons", "syringe_labeling_error", "is_a"),
    ("error_in_medication_process", "intercepted_error_status", "is_a"),
    ("intercepted_error_status", "drug_not_taken_intercepted_error", "is_a"),
    ("intercepted_error_status", "intercepted_medication_error", "is_a"),
    ("intercepted_error_status", "intercepted_product_dispensation_error", "is_a"),
    ("intercepted_error_status", "intercepted_drug_dispensation_error", "is_a"),
    ("intercepted_error_status", "intercepted_product_monitoring_error", "is_a"),
    ("intercepted_error_status", "intercepted_product_administration_error", "is_a"),
    ("intercepted_error_status", "intercepted_drug_administration_error", "is_a"),
    ("intercepted_error_status", "intercepted_product_prescribing_error", "is_a"),
    ("intercepted_error_status", "intercepted_product_selection_error", "is_a"),
    ("intercepted_error_status", "intercepted_drug_prescribing_error", "is_a"),
    ("intercepted_error_status", "intercepted_product_preparation_error", "is_a"),
    ("intercepted_error_status", "intercepted_product_storage_error", "is_a"),
    ("intercepted_error_status", "intercepted_wrong_patient_selected", "is_a"),
    ("intercepted_error_status", "intercepted_wrong_route_administration_selected", "is_a"),
    ("intercepted_error_status", "intercepted_wrong_dosage_form_selected", "is_a"),
    ("intercepted_error_status", "intercepted_wrong_drug_selected", "is_a"),
    ("intercepted_error_status", "intercepted_wrong_drug_product_selected", "is_a"),
    ("intercepted_error_status", "intercepted_wrong_drug_strength_selected", "is_a"),
    ("error_in_medication_process", "never_event_serious_reportable_event", "is_a"),
    ("never_event_serious_reportable_event", "high_alert_medication_error", "is_a"),
    ("error_in_medication_process", "vaccination_error", "is_a"),
    ("vaccination_error", "vaccine_preparation_error", "is_a")
]

# Graph erstellen
def create_graph(session):
    for name, node_data in node_dict.items():
        term = name.replace('_', ' ') # Unterstrich entfernen
        german_term = translate_to_german(name, node_data) # Begriffe übersetzen
        cui_data = get_cui_and_pso(term, node_data) # cui aufrufen und pso erstellen
        cui = cui_data.get('CUI', [None])[0]
        pso = cui_data.get('PSO', [None])[0]
        definition = escape_neo4j_string(get_definition(cui, term)) # Definition aufrufen/generieren
        synonyms = escape_neo4j_string(', '.join(get_synonyms(cui, term, node_data))) # Synonyme aufrufen/generieren

        # Cypherabfrage für die Erstellung der Knoten
        query = f"""
                CREATE ({name}:{name} {{
                    name: '{term}', 
                    CUI: '{cui}', 
                    PSO: '{pso}', 
                    german: '{german_term}', 
                    synonyms: '{synonyms}', 
                    definition: '{definition}'
                 }})
            """
        session.run(query)

    # Cypherabfrage für die Erstellung Beziehungen
    for subj, obj, rel in relationships:
        query = f"MATCH (a:{subj}), (b:{obj}) CREATE (a)-[:{rel}]->(b)"
        session.run(query)

# Begriffe übersetzen
def translate_to_german(name, node_data):
    translator = pipeline("translation_en_to_de", model="Helsinki-NLP/opus-mt-en-de", device=0)
    german_term = node_data.get('ger', '')
    if not german_term:
        german_term = translator(name.replace('_', ' '), max_length=40)[0]['translation_text']
    return german_term

def get_cui_and_pso(term, node_data):
    # Begriff standardisieren: entfernt Mehrzahlendungen wie "s", "es" und "ies" und wandelt Begriff in Kleinbuchstaben um
    normalized_term = re.sub(r'\b(ies|s|es)\b', '', term.lower()).strip()

    try:
        response = requests.get(full_search_url, params={'string': term, 'apiKey': apikey}) # GET- Anfrage an API
        response.raise_for_status() # für Fehler gibts eine Ausnahme
        items = response.json().get('result', {}).get('results', []) # JSON Antwort wird in Python-Objekte umgewandelt

        # Wenn Ergebnis nicht leer
        if items:
            for item in items:
                cui_name = item.get('name', '') # Name abrufen
                # Vergleich normalistiere Begriff  mit dem Begriff von UMLS
                if normalized_term == re.sub(r'\b(ies|s|es)\b', '', cui_name.lower()).strip():
                    cui = item['ui'] # Wenn gleich, dann cui speichern
                    # Ergebnisse als Dictionary zurückgeben
                    return {
                        'CUI': [cui],
                        'PSO': create_uid(term),
                        'definition': get_definition(cui, term),
                        'synonyms': get_synonyms(cui, term, node_data)
                    }

    except requests.exceptions.RequestException:
        pass # Fehler ignorieren

    # Standardrückgabewert bei fehlenden Ergebnissen/ Fehlern
    return {
        'PSO': create_uid(term),
        'definition': get_definition(None, term),  # Falls keine CUI vorhanden ist, verwende get_definition
        'synonyms': get_synonyms(None, term, node_data)  # Falls keine CUI vorhanden, suche in node_data nach Synonymen
    }

# Generierung ID für einen Begriff
def create_uid(name):
    name_bytes = name.encode('utf-8')
    hasher = hashlib.sha256()
    hasher.update(name_bytes)
    return [hasher.hexdigest()]

def get_definition(cui, term):
    # überprüfen, ob cui vorhanden
    if cui:
        definition_url = f"{uri}/rest/content/{version}/CUI/{cui}/definitions" # Definition- URL erstellen
        try:
            response = requests.get(definition_url, params={'apiKey': apikey}) # GET-Anfrage
            response.raise_for_status() # für Fehler gibts eine Ausnahme
            definitions = response.json().get('result', []) # JSON Antwort wird in Python-Objekte umgewandelt
            # erste Definition zurückgeben und Quelle dazu angeben
            if definitions:
                return f"{definitions[-1].get('value', '')} (Quelle: {definitions[-1].get('rootSource', 'Unknown')})"

        except requests.exceptions.RequestException:
            pass  # Fehler ignorierens

    # Kein CUI vorhanden, daher Fallback
    return askOllama("In the context of patient safety, define the term", term + "! Write three sentences!")

def get_synonyms(cui, term, node_data):
    # manuelle Synonyme aus node_dict abrufen
    manual_synonyms = node_data.get('synonyms', [])
    # wenn eine cui gefunden wird
    if cui:
        synonym_endpoint = f"/rest/content/{version}/CUI/{cui}/atoms" # URL definieren
        try:
            response = requests.get(uri + synonym_endpoint, params={'apiKey': apikey})
            response.raise_for_status()
            # Extrahieren der Namen der Synonyme und nach englisch und deutsch filtern
            atoms = response.json().get('result', [])
            umls_synonyms = [atom['name'] for atom in atoms if
                             'name' in atom and atom.get('language') in ['ENG', 'DEU']]
        except requests.exceptions.RequestException:
            umls_synonyms = [] # leere Liste wenn Fehler
    else:
        umls_synonyms = [] # leere Liste wenn keine cui

    # Kombination manuelle und UMLS-Synonyme & Duplikate entfernen
    all_synonyms = list(set(manual_synonyms + umls_synonyms))

    # wenn keine synonyme gefunden
    if not all_synonyms:
        # generiere 3 Synonyme mit AI und Kennzeichung, dass von AI erstellt
        ai_synonyms = askOllama(
            "List only 3 synonyms for the following term, separated by commas. Do not add any extra information:", term)
        return ai_synonyms

    return all_synonyms

def askOllama(task, term, model='openhermes',version= "2.5", temperature=0.1, role='user'):
    response = ollama.chat(model=model, messages=[{
        'role': role, # Rolle der Nachricht
        'content': f'{task}: {term}', # Aufgabe und Begriff ist der Inhalt
        'temperature': temperature, # Zufälligkeit der Antwort
        'top_p': 0.9, # Wahrscheinlichkeitsverteilung der Antwort
    }])

    result = response['message']['content']# Ergebnisse extrahieren
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Zeitstempel

    # Wenn in Aufgabe Wörter wie "synonyms" enthalten ist
    if "synonyms" in task.lower():
        # dann Antwort als Liste behandeln und mit (generated by AI) kennzeichnen
        return [f"{result} (generated with {model}, version {version}, at {timestamp})"]

    # Wenn in Aufgabe Wörter wie "define" enthalten ist
    if "define" in task.lower():
        # dann Antwort mit (generated by AI) kennzeichnen
        return f"{result} (generated with {model}, version {version}, at {timestamp})"
    else:
        return result

# Bereinigung von Zeichenfolgen (Vermeidung von Fehlern durch Sonderzeichen)
def escape_neo4j_string(s):
    if s is None:
        return ""
    return s.replace("'", "\\'").replace('"', '\\"')

if __name__ == "__main__":
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    try:
        with driver.session() as session:
            create_graph(session)
            print("Graph erfolgreich erstellt.")
    finally:
        driver.close()